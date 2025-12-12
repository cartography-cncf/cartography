from unittest.mock import MagicMock
from unittest.mock import patch

from kubernetes.client.models import V1ConfigMap

from cartography.intel.aws.iam import load_role_data
from cartography.intel.aws.iam import load_users
from cartography.intel.aws.iam import transform_role_trust_policies
from cartography.intel.aws.iam import transform_users
from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.eks import sync as sync_eks
from tests.data.kubernetes.eks import AWS_AUTH_CONFIGMAP_DATA
from tests.data.kubernetes.eks import MOCK_AWS_ROLES
from tests.data.kubernetes.eks import MOCK_AWS_USERS
from tests.data.kubernetes.eks import MOCK_CLUSTER_DATA
from tests.data.kubernetes.eks import MOCK_OIDC_PROVIDER
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
def test_eks_sync_creates_aws_role_relationships_and_oidc_providers(
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
    transformed_role_data = transform_role_trust_policies(
        MOCK_AWS_ROLES, TEST_ACCOUNT_ID
    )
    load_role_data(
        neo4j_session,
        transformed_role_data.role_data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Arrange: Set up prerequisite AWS Users in the graph
    transformed_user_data = transform_users(MOCK_AWS_USERS)
    load_users(
        neo4j_session,
        transformed_user_data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Arrange: Mock OIDC providers
    mock_get_oidc_provider.return_value = MOCK_OIDC_PROVIDER

    # Arrange: Create mock K8s client that returns our test ConfigMap
    mock_k8s_client = MagicMock()
    mock_k8s_client.name = TEST_CLUSTER_NAME
    mock_k8s_client.core.read_namespaced_config_map.return_value = (
        create_mock_aws_auth_configmap()
    )

    # Arrange: Create mock boto3 session
    mock_boto3_session = MagicMock()

    # Act: Run EKS sync
    sync_eks(
        neo4j_session,
        mock_k8s_client,
        mock_boto3_session,
        TEST_REGION,
        TEST_UPDATE_TAG,
        TEST_CLUSTER_ID,
        TEST_CLUSTER_NAME,
    )

    # Assert: Verify AWS Role to Kubernetes User relationships
    # Note: Only roles WITH explicit usernames should create user relationships
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
        ("arn:aws:iam::123456789012:role/EKSServiceRole", "test-cluster/services"),
        ("arn:aws:iam::123456789012:role/EKSServiceRole", "test-cluster/automation"),
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
    expected_user_user_relationships = {
        ("arn:aws:iam::123456789012:user/alice", "test-cluster/alice-user"),
        ("arn:aws:iam::123456789012:user/bob", "test-cluster/bob-user"),
        ("arn:aws:iam::123456789012:user/charlie", "test-cluster/charlie-user"),
    }

    actual_user_user_relationships = check_rels(
        neo4j_session,
        "AWSUser",
        "arn",
        "KubernetesUser",
        "id",
        "MAPS_TO",
    )
    assert expected_user_user_relationships.issubset(actual_user_user_relationships)

    # Assert: Verify AWS User to Kubernetes Group relationships
    expected_user_group_relationships = {
        ("arn:aws:iam::123456789012:user/alice", "test-cluster/developers"),
        ("arn:aws:iam::123456789012:user/alice", "test-cluster/dev-team"),
        ("arn:aws:iam::123456789012:user/bob", "test-cluster/system:masters"),
        ("arn:aws:iam::123456789012:user/charlie", "test-cluster/view-only"),
        ("arn:aws:iam::123456789012:user/charlie", "test-cluster/readonly"),
        ("arn:aws:iam::123456789012:user/dana", "test-cluster/support-team"),
        ("arn:aws:iam::123456789012:user/service-account", "test-cluster/services"),
    }

    actual_user_group_relationships = check_rels(
        neo4j_session,
        "AWSUser",
        "arn",
        "KubernetesGroup",
        "id",
        "MAPS_TO",
    )
    assert expected_user_group_relationships.issubset(actual_user_group_relationships)

    # Assert: Verify OIDC Provider nodes were created
    expected_oidc_providers = {
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

    # Note: OIDC Provider nodes only contain infrastructure metadata.
    # Identity relationships (OktaUser/Group -> KubernetesUser/Group) are handled
    # by the respective data models and Okta module, not by the EKS module.
