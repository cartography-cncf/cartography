from unittest.mock import MagicMock
from unittest.mock import patch

from kubernetes.client.models import V1ConfigMap

from cartography.intel.aws.iam import load_roles
from cartography.intel.aws.iam import load_users
from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.eks import sync as eks_sync
from tests.data.kubernetes.eks import AWS_AUTH_CONFIGMAP_DATA
from tests.data.kubernetes.eks import MOCK_ADDITIONAL_AWS_ROLES
from tests.data.kubernetes.eks import MOCK_ADDITIONAL_AWS_USERS
from tests.data.kubernetes.eks import MOCK_AWS_ROLES
from tests.data.kubernetes.eks import MOCK_AWS_USERS
from tests.data.kubernetes.eks import MOCK_CLUSTER_DATA
from tests.data.kubernetes.eks import MOCK_KUBERNETES_USERS_FROM_RBAC
from tests.data.kubernetes.eks import MOCK_OIDC_PROVIDERS
from tests.data.kubernetes.eks import TEST_ACCOUNT_ID
from tests.data.kubernetes.eks import TEST_CLUSTER_ID
from tests.data.kubernetes.eks import TEST_CLUSTER_NAME
from tests.data.kubernetes.eks import TEST_REGION
from tests.data.kubernetes.eks import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def create_mock_aws_auth_configmap():
    """Create a mock V1ConfigMap object for testing."""
    return V1ConfigMap(
        api_version="v1",
        kind="ConfigMap",
        metadata={"name": "aws-auth", "namespace": "kube-system"},
        data=AWS_AUTH_CONFIGMAP_DATA,
    )


@patch("cartography.intel.kubernetes.eks.get_oidc_provider")
@patch("cartography.intel.kubernetes.eks.transform_users")
@patch("cartography.intel.kubernetes.eks.get_cluster_role_bindings")
@patch("cartography.intel.kubernetes.eks.get_role_bindings")
def test_eks_sync_creates_aws_role_relationships_and_oidc_providers(
    mock_get_role_bindings,
    mock_get_cluster_role_bindings,
    mock_transform_users,
    mock_get_oidc_provider,
    neo4j_session,
):
    """
    Test that EKS sync creates the expected AWS Role/User to Kubernetes User/Group relationships
    and OIDC provider infrastructure nodes with cluster relationships.
    """
    # Arrange: Create AWS Account first (required for role loading)
    neo4j_session.run(
        """
        MERGE (aa:AWSAccount{id: $account_id})
        ON CREATE SET aa.firstseen = timestamp()
        SET aa.lastupdated = $update_tag
        """,
        account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Arrange: Create cluster (required for OIDC provider relationships)
    load_kubernetes_cluster(neo4j_session, MOCK_CLUSTER_DATA, TEST_UPDATE_TAG)

    # Arrange: Set up prerequisite AWS Roles in the graph
    load_roles(
        neo4j_session,
        MOCK_AWS_ROLES,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Arrange: Set up prerequisite AWS Users in the graph
    load_users(
        neo4j_session,
        MOCK_AWS_USERS,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Arrange: Set up additional AWS Roles and Users for mapAccounts testing
    load_roles(
        neo4j_session,
        MOCK_ADDITIONAL_AWS_ROLES,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    load_users(
        neo4j_session,
        MOCK_ADDITIONAL_AWS_USERS,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Arrange: Mock RBAC functions to return test users for mapAccounts
    mock_get_role_bindings.return_value = []  # Empty role bindings
    mock_get_cluster_role_bindings.return_value = []  # Empty cluster role bindings
    mock_transform_users.return_value = MOCK_KUBERNETES_USERS_FROM_RBAC

    # Arrange: Mock OIDC providers
    mock_get_oidc_provider.return_value = MOCK_OIDC_PROVIDERS

    # Arrange: Create mock K8s client that returns our test ConfigMap
    mock_k8s_client = MagicMock()
    mock_k8s_client.name = TEST_CLUSTER_NAME
    mock_k8s_client.core.read_namespaced_config_map.return_value = (
        create_mock_aws_auth_configmap()
    )

    # Arrange: Create mock boto3 session
    mock_boto3_session = MagicMock()

    # Act: Run EKS sync
    eks_sync(
        neo4j_session,
        mock_k8s_client,
        mock_boto3_session,
        TEST_REGION,
        TEST_UPDATE_TAG,
        TEST_CLUSTER_ID,
        TEST_CLUSTER_NAME,
    )

    # Assert: Verify AWS Role to Kubernetes User relationships
    expected_user_relationships = {
        ("arn:aws:iam::123456789012:role/EKSDevRole", "test-cluster/dev-user"),
        ("arn:aws:iam::123456789012:role/EKSAdminRole", "test-cluster/admin-user"),
        ("arn:aws:iam::123456789012:role/EKSViewerRole", "test-cluster/viewer-user"),
    }

    actual_user_relationships = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "KubernetesUser",
        "id",
        "MAPS_TO",
    )
    assert expected_user_relationships.issubset(actual_user_relationships)

    # Assert: Verify AWS Role to Kubernetes Group relationships
    expected_group_relationships = {
        ("arn:aws:iam::123456789012:role/EKSDevRole", "test-cluster/developers"),
        ("arn:aws:iam::123456789012:role/EKSDevRole", "test-cluster/staging-access"),
        ("arn:aws:iam::123456789012:role/EKSAdminRole", "test-cluster/system:masters"),
        ("arn:aws:iam::123456789012:role/EKSViewerRole", "test-cluster/view-only"),
        ("arn:aws:iam::123456789012:role/EKSViewerRole", "test-cluster/read-access"),
        ("arn:aws:iam::123456789012:role/EKSGroupOnlyRole", "test-cluster/ci-cd"),
        ("arn:aws:iam::123456789012:role/EKSGroupOnlyRole", "test-cluster/automation"),
    }

    actual_group_relationships = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "KubernetesGroup",
        "id",
        "MAPS_TO",
    )
    assert expected_group_relationships.issubset(actual_group_relationships)

    # Assert: Verify AWS User to Kubernetes User relationships
    expected_aws_user_to_k8s_user_relationships = {
        ("arn:aws:iam::123456789012:user/alice", "test-cluster/alice-user"),
        ("arn:aws:iam::123456789012:user/bob", "test-cluster/bob-user"),
        (
            "arn:aws:iam::123456789012:user/charlie",
            "test-cluster/arn:aws:iam::123456789012:user/charlie",
        ),  # No username specified, defaults to ARN
    }

    actual_aws_user_to_k8s_user_relationships = check_rels(
        neo4j_session,
        "AWSUser",
        "arn",
        "KubernetesUser",
        "id",
        "MAPS_TO",
    )
    assert expected_aws_user_to_k8s_user_relationships.issubset(
        actual_aws_user_to_k8s_user_relationships
    )

    # Assert: Verify AWS User to Kubernetes Group relationships
    expected_aws_user_to_k8s_group_relationships = {
        ("arn:aws:iam::123456789012:user/alice", "test-cluster/developers"),
        ("arn:aws:iam::123456789012:user/alice", "test-cluster/qa-access"),
        ("arn:aws:iam::123456789012:user/bob", "test-cluster/system:masters"),
        ("arn:aws:iam::123456789012:user/charlie", "test-cluster/read-only"),
        ("arn:aws:iam::123456789012:user/charlie", "test-cluster/monitoring"),
    }

    actual_aws_user_to_k8s_group_relationships = check_rels(
        neo4j_session,
        "AWSUser",
        "arn",
        "KubernetesGroup",
        "id",
        "MAPS_TO",
    )
    assert expected_aws_user_to_k8s_group_relationships.issubset(
        actual_aws_user_to_k8s_group_relationships
    )

    # Assert: Verify templated AccountID processing for AWS Role to Kubernetes User relationships
    expected_templated_role_to_user_relationships = {
        (
            "arn:aws:iam::123456789012:role/EKSTemplatedRole",
            "test-cluster/templated-user-123456789012",
        ),
    }

    actual_templated_role_to_user_relationships = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "KubernetesUser",
        "id",
        "MAPS_TO",
    )
    assert expected_templated_role_to_user_relationships.issubset(
        actual_templated_role_to_user_relationships
    )

    # Assert: Verify templated AccountID processing for AWS Role to Kubernetes Group relationships
    expected_templated_role_to_group_relationships = {
        (
            "arn:aws:iam::123456789012:role/EKSTemplatedRole",
            "test-cluster/templated-group-123456789012",
        ),
        (
            "arn:aws:iam::123456789012:role/EKSTemplatedRole",
            "test-cluster/system:authenticated",
        ),
    }

    actual_templated_role_to_group_relationships = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "KubernetesGroup",
        "id",
        "MAPS_TO",
    )
    assert expected_templated_role_to_group_relationships.issubset(
        actual_templated_role_to_group_relationships
    )

    # Assert: Verify templated AccountID processing for AWS User to Kubernetes User relationships
    expected_templated_user_to_user_relationships = {
        (
            "arn:aws:iam::123456789012:user/templated-user",
            "test-cluster/service-123456789012",
        ),
    }

    actual_templated_user_to_user_relationships = check_rels(
        neo4j_session,
        "AWSUser",
        "arn",
        "KubernetesUser",
        "id",
        "MAPS_TO",
    )
    assert expected_templated_user_to_user_relationships.issubset(
        actual_templated_user_to_user_relationships
    )

    # Assert: Verify templated AccountID processing for AWS User to Kubernetes Group relationships
    expected_templated_user_to_group_relationships = {
        (
            "arn:aws:iam::123456789012:user/templated-user",
            "test-cluster/templated-access-123456789012",
        ),
    }

    actual_templated_user_to_group_relationships = check_rels(
        neo4j_session,
        "AWSUser",
        "arn",
        "KubernetesGroup",
        "id",
        "MAPS_TO",
    )
    assert expected_templated_user_to_group_relationships.issubset(
        actual_templated_user_to_group_relationships
    )

    # Assert: Verify OIDC Provider nodes were created
    expected_oidc_providers = {
        (
            f"{TEST_CLUSTER_NAME}/oidc/auth0-provider",
            "https://company.auth0.com/",
            "auth0-provider",
            "eks",
        ),
        (
            f"{TEST_CLUSTER_NAME}/oidc/okta-provider",
            "https://company.okta.com/oauth2/default",
            "okta-provider",
            "eks",
        ),
    }
    actual_oidc_providers = check_nodes(
        neo4j_session,
        "KubernetesOIDCProvider",
        ["id", "issuer_url", "name", "k8s_platform"],
    )
    assert expected_oidc_providers.issubset(actual_oidc_providers)

    # Assert: Verify Cluster TRUSTS OIDC Provider relationships
    expected_cluster_relationships = {
        (TEST_CLUSTER_ID, f"{TEST_CLUSTER_NAME}/oidc/auth0-provider"),
        (TEST_CLUSTER_ID, f"{TEST_CLUSTER_NAME}/oidc/okta-provider"),
    }
    actual_cluster_relationships = check_rels(
        neo4j_session,
        "KubernetesCluster",
        "id",
        "KubernetesOIDCProvider",
        "id",
        "TRUSTS",
    )
    assert expected_cluster_relationships.issubset(actual_cluster_relationships)

    # Assert: Verify mapAccounts relationships - AWS Roles from allowed accounts
    expected_mapaccounts_role_relationships = {
        (
            "arn:aws:iam::123456789012:role/ProductionRole",
            "test-cluster/arn:aws:iam::123456789012:role/ProductionRole",
        ),
        (
            "arn:aws:iam::999888777666:role/CrossAccountRole",
            "test-cluster/arn:aws:iam::999888777666:role/CrossAccountRole",
        ),
    }
    actual_mapaccounts_role_relationships = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "KubernetesUser",
        "id",
        "MAPS_TO",
    )
    assert expected_mapaccounts_role_relationships.issubset(
        actual_mapaccounts_role_relationships
    )

    # Assert: Verify mapAccounts relationships - AWS Users from allowed accounts
    expected_mapaccounts_user_relationships = {
        (
            "arn:aws:iam::123456789012:user/service-account-user",
            "test-cluster/arn:aws:iam::123456789012:user/service-account-user",
        ),
    }
    actual_mapaccounts_user_relationships = check_rels(
        neo4j_session,
        "AWSUser",
        "arn",
        "KubernetesUser",
        "id",
        "MAPS_TO",
    )
    assert expected_mapaccounts_user_relationships.issubset(
        actual_mapaccounts_user_relationships
    )

    # Assert: Verify SessionNameRaw templated role to user relationships
    expected_session_role_to_user_relationships = {
        # admin:{{SessionNameRaw}} should match admin:alice and admin:bob@company.com
        (
            "arn:aws:iam::123456789012:role/EKSSessionNameRawRole",
            "test-cluster/admin:alice",
        ),
        (
            "arn:aws:iam::123456789012:role/EKSSessionNameRawRole",
            "test-cluster/admin:bob@company.com",
        ),
        # {{SessionNameRaw}} should match charlie and dave.smith
        (
            "arn:aws:iam::123456789012:role/EKSPureSessionNameRawRole",
            "test-cluster/charlie",
        ),
        (
            "arn:aws:iam::123456789012:role/EKSPureSessionNameRawRole",
            "test-cluster/dave.smith",
        ),
    }

    actual_session_role_to_user_relationships = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "KubernetesUser",
        "id",
        "MAPS_TO",
    )
    assert expected_session_role_to_user_relationships.issubset(
        actual_session_role_to_user_relationships
    )

    # Assert: Verify SessionNameRaw templated role to group relationships
    expected_session_role_to_group_relationships = {
        # admin:{{SessionNameRaw}} creates system:masters groups
        (
            "arn:aws:iam::123456789012:role/EKSSessionNameRawRole",
            "test-cluster/system:masters",
        ),
        # session-group:{{SessionNameRaw}} should create groups for each matched user
        (
            "arn:aws:iam::123456789012:role/EKSSessionNameRawRole",
            "test-cluster/session-group:alice",
        ),
        (
            "arn:aws:iam::123456789012:role/EKSSessionNameRawRole",
            "test-cluster/session-group:bob@company.com",
        ),
        # {{SessionNameRaw}} creates federated-users groups
        (
            "arn:aws:iam::123456789012:role/EKSPureSessionNameRawRole",
            "test-cluster/federated-users",
        ),
    }

    actual_session_role_to_group_relationships = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "KubernetesGroup",
        "id",
        "MAPS_TO",
    )
    assert expected_session_role_to_group_relationships.issubset(
        actual_session_role_to_group_relationships
    )

    # Assert: Verify SessionNameRaw templated user to user relationships
    expected_session_user_to_user_relationships = {
        # svc:{{SessionNameRaw}} should match svc:automation and svc:monitoring@company.com
        ("arn:aws:iam::123456789012:user/session-user", "test-cluster/svc:automation"),
        (
            "arn:aws:iam::123456789012:user/session-user",
            "test-cluster/svc:monitoring@company.com",
        ),
    }

    actual_session_user_to_user_relationships = check_rels(
        neo4j_session,
        "AWSUser",
        "arn",
        "KubernetesUser",
        "id",
        "MAPS_TO",
    )
    assert expected_session_user_to_user_relationships.issubset(
        actual_session_user_to_user_relationships
    )

    # Assert: Verify SessionNameRaw templated user to group relationships
    expected_session_user_to_group_relationships = {
        # svc:{{SessionNameRaw}} creates service-accounts groups
        (
            "arn:aws:iam::123456789012:user/session-user",
            "test-cluster/service-accounts",
        ),
    }

    actual_session_user_to_group_relationships = check_rels(
        neo4j_session,
        "AWSUser",
        "arn",
        "KubernetesGroup",
        "id",
        "MAPS_TO",
    )
    assert expected_session_user_to_group_relationships.issubset(
        actual_session_user_to_group_relationships
    )

    # Assert: Verify mixed template (AccountID + SessionNameRaw) role to user relationships
    expected_mixed_role_to_user_relationships = {
        # user-{{AccountID}}-{{SessionNameRaw}} should match user-123456789012-alice and user-123456789012-bob@company.com
        (
            "arn:aws:iam::123456789012:role/EKSMixedTemplateRole",
            "test-cluster/user-123456789012-alice",
        ),
        (
            "arn:aws:iam::123456789012:role/EKSMixedTemplateRole",
            "test-cluster/user-123456789012-bob@company.com",
        ),
    }

    actual_mixed_role_to_user_relationships = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "KubernetesUser",
        "id",
        "MAPS_TO",
    )
    assert expected_mixed_role_to_user_relationships.issubset(
        actual_mixed_role_to_user_relationships
    )

    # Assert: Verify mixed template role to group relationships
    expected_mixed_role_to_group_relationships = {
        # mixed-group-{{AccountID}}-{{SessionNameRaw}} should resolve correctly for each matched user
        (
            "arn:aws:iam::123456789012:role/EKSMixedTemplateRole",
            "test-cluster/mixed-group-123456789012-alice",
        ),
        (
            "arn:aws:iam::123456789012:role/EKSMixedTemplateRole",
            "test-cluster/mixed-group-123456789012-bob@company.com",
        ),
        # system:authenticated should be created for both matches
        (
            "arn:aws:iam::123456789012:role/EKSMixedTemplateRole",
            "test-cluster/system:authenticated",
        ),
    }

    actual_mixed_role_to_group_relationships = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "KubernetesGroup",
        "id",
        "MAPS_TO",
    )
    assert expected_mixed_role_to_group_relationships.issubset(
        actual_mixed_role_to_group_relationships
    )

    # Assert: Verify SessionName templated role to user relationships
    expected_session_name_role_to_user_relationships = {
        # admin:{{SessionName}} should match admin:alice-company-com and admin:bob-example-org
        (
            "arn:aws:iam::123456789012:role/EKSSessionNameRole",
            "test-cluster/admin:alice-company-com",
        ),
        (
            "arn:aws:iam::123456789012:role/EKSSessionNameRole",
            "test-cluster/admin:bob-example-org",
        ),
        # {{SessionName}} should match charlie-smith and dave-jones
        (
            "arn:aws:iam::123456789012:role/EKSPureSessionNameRole",
            "test-cluster/charlie-smith",
        ),
        (
            "arn:aws:iam::123456789012:role/EKSPureSessionNameRole",
            "test-cluster/dave-jones",
        ),
    }

    actual_session_name_role_to_user_relationships = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "KubernetesUser",
        "id",
        "MAPS_TO",
    )
    assert expected_session_name_role_to_user_relationships.issubset(
        actual_session_name_role_to_user_relationships
    )

    # Assert: Verify SessionName templated role to group relationships
    expected_session_name_role_to_group_relationships = {
        # admin:{{SessionName}} creates system:masters groups
        (
            "arn:aws:iam::123456789012:role/EKSSessionNameRole",
            "test-cluster/system:masters",
        ),
        # session-group:{{SessionName}} should create groups for each matched user
        (
            "arn:aws:iam::123456789012:role/EKSSessionNameRole",
            "test-cluster/session-group:alice-company-com",
        ),
        (
            "arn:aws:iam::123456789012:role/EKSSessionNameRole",
            "test-cluster/session-group:bob-example-org",
        ),
        # {{SessionName}} creates federated-users groups
        (
            "arn:aws:iam::123456789012:role/EKSPureSessionNameRole",
            "test-cluster/federated-users",
        ),
    }

    actual_session_name_role_to_group_relationships = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "KubernetesGroup",
        "id",
        "MAPS_TO",
    )
    assert expected_session_name_role_to_group_relationships.issubset(
        actual_session_name_role_to_group_relationships
    )

    # Assert: Verify mixed SessionName template (AccountID + SessionName) role to user relationships
    expected_mixed_session_name_role_to_user_relationships = {
        # user-{{AccountID}}-{{SessionName}} should match user-123456789012-alice-company-com and user-123456789012-bob-example-org
        (
            "arn:aws:iam::123456789012:role/EKSMixedSessionNameRole",
            "test-cluster/user-123456789012-alice-company-com",
        ),
        (
            "arn:aws:iam::123456789012:role/EKSMixedSessionNameRole",
            "test-cluster/user-123456789012-bob-example-org",
        ),
    }

    actual_mixed_session_name_role_to_user_relationships = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "KubernetesUser",
        "id",
        "MAPS_TO",
    )
    assert expected_mixed_session_name_role_to_user_relationships.issubset(
        actual_mixed_session_name_role_to_user_relationships
    )

    # Assert: Verify mixed SessionName template role to group relationships
    expected_mixed_session_name_role_to_group_relationships = {
        # mixed-group-{{AccountID}}-{{SessionName}} should resolve correctly for each matched user
        (
            "arn:aws:iam::123456789012:role/EKSMixedSessionNameRole",
            "test-cluster/mixed-group-123456789012-alice-company-com",
        ),
        (
            "arn:aws:iam::123456789012:role/EKSMixedSessionNameRole",
            "test-cluster/mixed-group-123456789012-bob-example-org",
        ),
        # system:authenticated should be created for both matches
        (
            "arn:aws:iam::123456789012:role/EKSMixedSessionNameRole",
            "test-cluster/system:authenticated",
        ),
    }

    actual_mixed_session_name_role_to_group_relationships = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "KubernetesGroup",
        "id",
        "MAPS_TO",
    )
    assert expected_mixed_session_name_role_to_group_relationships.issubset(
        actual_mixed_session_name_role_to_group_relationships
    )

    # Assert: Verify SessionName templated user to user relationships
    expected_session_name_user_to_user_relationships = {
        # svc:{{SessionName}} should match svc:automation-service and svc:monitoring-prod
        (
            "arn:aws:iam::123456789012:user/session-name-user",
            "test-cluster/svc:automation-service",
        ),
        (
            "arn:aws:iam::123456789012:user/session-name-user",
            "test-cluster/svc:monitoring-prod",
        ),
    }

    actual_session_name_user_to_user_relationships = check_rels(
        neo4j_session,
        "AWSUser",
        "arn",
        "KubernetesUser",
        "id",
        "MAPS_TO",
    )
    assert expected_session_name_user_to_user_relationships.issubset(
        actual_session_name_user_to_user_relationships
    )

    # Assert: Verify SessionName templated user to group relationships
    expected_session_name_user_to_group_relationships = {
        # svc:{{SessionName}} creates service-accounts groups
        (
            "arn:aws:iam::123456789012:user/session-name-user",
            "test-cluster/service-accounts",
        ),
    }

    actual_session_name_user_to_group_relationships = check_rels(
        neo4j_session,
        "AWSUser",
        "arn",
        "KubernetesGroup",
        "id",
        "MAPS_TO",
    )
    assert expected_session_name_user_to_group_relationships.issubset(
        actual_session_name_user_to_group_relationships
    )

    # Note: OIDC Provider nodes only contain infrastructure metadata.
    # Identity relationships (OktaUser/Group -> KubernetesUser/Group) are handled
    # by the respective data models and Okta module, not by the EKS module.
