from unittest.mock import MagicMock
from unittest.mock import patch

from kubernetes.client.exceptions import ApiException
from kubernetes.client.models import V1ConfigMap

from cartography.intel.aws.iam import load_role_data
from cartography.intel.aws.iam import load_users
from cartography.intel.aws.iam import transform_role_trust_policies
from cartography.intel.aws.iam import transform_users
from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.eks import sync as sync_eks
from tests.data.kubernetes.eks import AWS_AUTH_CONFIGMAP_DATA
from tests.data.kubernetes.eks import MOCK_ACCESS_ENTRIES
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

TEST_CLUSTER_ARN = (
    f"arn:aws:eks:{TEST_REGION}:{TEST_ACCOUNT_ID}:cluster/{TEST_CLUSTER_NAME}"
)


def create_mock_aws_auth_configmap():
    """Create a mock V1ConfigMap object for testing."""
    return V1ConfigMap(
        api_version="v1",
        kind="ConfigMap",
        metadata={"name": "aws-auth", "namespace": "kube-system"},
        data=AWS_AUTH_CONFIGMAP_DATA,
    )


def create_custom_aws_auth_configmap(data):
    return V1ConfigMap(
        api_version="v1",
        kind="ConfigMap",
        metadata={"name": "aws-auth", "namespace": "kube-system"},
        data=data,
    )


@patch("cartography.intel.kubernetes.eks.get_access_entries")
@patch("cartography.intel.kubernetes.eks.get_oidc_provider")
def test_eks_sync_creates_aws_role_relationships_and_oidc_providers(
    mock_get_oidc_provider,
    mock_get_access_entries,
    neo4j_session,
):
    """
    Test that EKS sync creates the expected AWS Role/User to Kubernetes User/Group relationships
    from aws-auth ConfigMap, Access Entries, and OIDC provider infrastructure nodes with cluster relationships.
    """
    # Arrange: Create AWS Account first (required for role loading)
    neo4j_session.run(
        """
        MERGE (aa:AWSAccount{id: $account_id})
        ON CREATE SET aa.firstseen = timestamp()
        SET aa.lastupdated = $update_tag, aa :Tenant
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

    # Arrange: Mock Access Entries
    mock_get_access_entries.return_value = MOCK_ACCESS_ENTRIES

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
        TEST_CLUSTER_ARN,
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

    # Assert: Verify users from Access Entries are created
    expected_access_entry_users = {
        ("test-cluster/alice-access-entry", "alice-access-entry"),
        ("test-cluster/access-role-user", "access-role-user"),
        ("test-cluster/bob-access-entry", "bob-access-entry"),
        (
            "test-cluster/arn:aws:iam::123456789012:role/EKSViewerRole",
            "arn:aws:iam::123456789012:role/EKSViewerRole",
        ),
    }
    actual_access_entry_users = check_nodes(
        neo4j_session,
        "KubernetesUser",
        ["id", "name"],
    )
    assert expected_access_entry_users.issubset(actual_access_entry_users)

    # Assert: Verify groups from Access Entries are created
    expected_access_entry_groups = {
        ("test-cluster/access-entry-devs", "access-entry-devs"),
        ("test-cluster/access-entry-team", "access-entry-team"),
        ("test-cluster/access-entry-admins", "access-entry-admins"),
        ("test-cluster/platform-team", "platform-team"),
        ("test-cluster/viewers", "viewers"),
        ("test-cluster/readonly-access", "readonly-access"),
    }
    actual_access_entry_groups = check_nodes(
        neo4j_session,
        "KubernetesGroup",
        ["id", "name"],
    )
    assert expected_access_entry_groups.issubset(actual_access_entry_groups)

    # Assert: Verify Access Entry AWS User to Kubernetes User relationships
    expected_access_entry_user_relationships = {
        ("arn:aws:iam::123456789012:user/alice", "test-cluster/alice-access-entry"),
        ("arn:aws:iam::123456789012:user/bob", "test-cluster/bob-access-entry"),
    }
    actual_access_entry_user_relationships = check_rels(
        neo4j_session,
        "AWSUser",
        "arn",
        "KubernetesUser",
        "id",
        "MAPS_TO",
    )
    assert expected_access_entry_user_relationships.issubset(
        actual_access_entry_user_relationships
    )

    # Assert: Verify Access Entry AWS Role to Kubernetes User relationships
    expected_access_entry_role_user_relationships = {
        (
            "arn:aws:iam::123456789012:role/EKSAccessRole",
            "test-cluster/access-role-user",
        ),
        (
            "arn:aws:iam::123456789012:role/EKSViewerRole",
            "test-cluster/arn:aws:iam::123456789012:role/EKSViewerRole",
        ),
    }
    actual_access_entry_role_user_relationships = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "KubernetesUser",
        "id",
        "MAPS_TO",
    )
    assert expected_access_entry_role_user_relationships.issubset(
        actual_access_entry_role_user_relationships
    )

    # Assert: Verify Access Entry AWS User to Kubernetes Group relationships
    expected_access_entry_user_group_relationships = {
        ("arn:aws:iam::123456789012:user/alice", "test-cluster/access-entry-devs"),
        ("arn:aws:iam::123456789012:user/alice", "test-cluster/access-entry-team"),
    }
    actual_access_entry_user_group_relationships = check_rels(
        neo4j_session,
        "AWSUser",
        "arn",
        "KubernetesGroup",
        "id",
        "MAPS_TO",
    )
    assert expected_access_entry_user_group_relationships.issubset(
        actual_access_entry_user_group_relationships
    )

    # Assert: Verify Access Entry AWS Role to Kubernetes Group relationships
    expected_access_entry_role_group_relationships = {
        (
            "arn:aws:iam::123456789012:role/EKSAccessRole",
            "test-cluster/access-entry-admins",
        ),
        ("arn:aws:iam::123456789012:role/EKSAccessRole", "test-cluster/platform-team"),
        ("arn:aws:iam::123456789012:role/EKSViewerRole", "test-cluster/viewers"),
        (
            "arn:aws:iam::123456789012:role/EKSViewerRole",
            "test-cluster/readonly-access",
        ),
    }
    actual_access_entry_role_group_relationships = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "KubernetesGroup",
        "id",
        "MAPS_TO",
    )
    assert expected_access_entry_role_group_relationships.issubset(
        actual_access_entry_role_group_relationships
    )


@patch("cartography.intel.kubernetes.eks.get_access_entries", return_value=[])
@patch("cartography.intel.kubernetes.eks.get_oidc_provider", return_value=[])
def test_eks_sync_resolves_supported_aws_auth_templates(
    mock_get_oidc_provider,
    mock_get_access_entries,
    neo4j_session,
):
    neo4j_session.run(
        """
        MERGE (aa:AWSAccount{id: $account_id})
        ON CREATE SET aa.firstseen = timestamp()
        SET aa.lastupdated = $update_tag, aa :Tenant
        """,
        account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    load_kubernetes_cluster(neo4j_session, MOCK_CLUSTER_DATA, TEST_UPDATE_TAG)

    for role_arn in (
        f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/TemplateAccountRole",
        f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/TemplateSessionRole",
        f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/TemplateSessionRawRole",
    ):
        neo4j_session.run(
            """
            MERGE (role:AWSRole {arn: $arn})
            SET role.id = $arn, role.lastupdated = $update_tag
            """,
            arn=role_arn,
            update_tag=TEST_UPDATE_TAG,
        )

    neo4j_session.run(
        """
        MERGE (user:AWSUser {arn: $arn})
        SET user.id = $arn, user.lastupdated = $update_tag
        """,
        arn=f"arn:aws:iam::{TEST_ACCOUNT_ID}:user/template-user",
        update_tag=TEST_UPDATE_TAG,
    )

    neo4j_session.run(
        """
        UNWIND $users AS user
        MERGE (u:KubernetesUser {id: user.id})
        SET u.name = user.name,
            u.cluster_name = $cluster_name,
            u.lastupdated = $update_tag
        WITH u
        MATCH (c:KubernetesCluster {id: $cluster_id})
        MERGE (c)-[:RESOURCE]->(u)
        """,
        users=[
            {
                "id": f"{TEST_CLUSTER_NAME}/sso:alice-example.com",
                "name": "sso:alice-example.com",
            },
            {
                "id": f"{TEST_CLUSTER_NAME}/raw:alice@example.com",
                "name": "raw:alice@example.com",
            },
            {
                "id": f"{TEST_CLUSTER_NAME}/sso:alice@example.com",
                "name": "sso:alice@example.com",
            },
        ],
        cluster_name=TEST_CLUSTER_NAME,
        cluster_id=TEST_CLUSTER_ID,
        update_tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        UNWIND $groups AS group
        MERGE (g:KubernetesGroup {id: group.id})
        SET g.name = group.name,
            g.cluster_name = $cluster_name,
            g.lastupdated = $update_tag
        WITH g
        MATCH (c:KubernetesCluster {id: $cluster_id})
        MERGE (c)-[:RESOURCE]->(g)
        """,
        groups=[
            {
                "id": f"{TEST_CLUSTER_NAME}/team:alice-example.com",
                "name": "team:alice-example.com",
            },
            {
                "id": f"{TEST_CLUSTER_NAME}/raw-team:alice@example.com",
                "name": "raw-team:alice@example.com",
            },
            {
                "id": f"{TEST_CLUSTER_NAME}/team:alice@example.com",
                "name": "team:alice@example.com",
            },
        ],
        cluster_name=TEST_CLUSTER_NAME,
        cluster_id=TEST_CLUSTER_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    mock_k8s_client = MagicMock()
    mock_k8s_client.name = TEST_CLUSTER_NAME
    mock_k8s_client.core.read_namespaced_config_map.return_value = create_custom_aws_auth_configmap(
        {
            "mapRoles": f"""
- rolearn: arn:aws:iam::{TEST_ACCOUNT_ID}:role/TemplateAccountRole
  username: acct-{{{{AccountID}}}}-admin
  groups:
  - acct-{{{{AccountID}}}}-admins
- rolearn: arn:aws:iam::{TEST_ACCOUNT_ID}:role/TemplateSessionRole
  username: sso:{{{{SessionName}}}}
  groups:
  - team:{{{{SessionName}}}}
- rolearn: arn:aws:iam::{TEST_ACCOUNT_ID}:role/TemplateSessionRawRole
  username: raw:{{{{SessionNameRaw}}}}
  groups:
  - raw-team:{{{{SessionNameRaw}}}}
""",
            "mapUsers": f"""
- userarn: arn:aws:iam::{TEST_ACCOUNT_ID}:user/template-user
  username: acct-user-{{{{AccountID}}}}
  groups:
  - acct-group-{{{{AccountID}}}}
""",
        }
    )

    sync_eks(
        neo4j_session,
        mock_k8s_client,
        MagicMock(),
        TEST_REGION,
        TEST_UPDATE_TAG,
        TEST_CLUSTER_ID,
        TEST_CLUSTER_ARN,
    )

    actual_role_user_relationships = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "KubernetesUser",
        "id",
        "MAPS_TO",
    )
    assert {
        (
            f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/TemplateAccountRole",
            f"{TEST_CLUSTER_NAME}/acct-{TEST_ACCOUNT_ID}-admin",
        ),
        (
            f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/TemplateSessionRole",
            f"{TEST_CLUSTER_NAME}/sso:alice-example.com",
        ),
        (
            f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/TemplateSessionRawRole",
            f"{TEST_CLUSTER_NAME}/raw:alice@example.com",
        ),
    }.issubset(actual_role_user_relationships)

    actual_role_group_relationships = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "KubernetesGroup",
        "id",
        "MAPS_TO",
    )
    assert {
        (
            f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/TemplateAccountRole",
            f"{TEST_CLUSTER_NAME}/acct-{TEST_ACCOUNT_ID}-admins",
        ),
        (
            f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/TemplateSessionRole",
            f"{TEST_CLUSTER_NAME}/team:alice-example.com",
        ),
        (
            f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/TemplateSessionRawRole",
            f"{TEST_CLUSTER_NAME}/raw-team:alice@example.com",
        ),
    }.issubset(actual_role_group_relationships)

    actual_user_group_relationships = check_rels(
        neo4j_session,
        "AWSUser",
        "arn",
        "KubernetesGroup",
        "id",
        "MAPS_TO",
    )
    assert {
        (
            f"arn:aws:iam::{TEST_ACCOUNT_ID}:user/template-user",
            f"{TEST_CLUSTER_NAME}/acct-group-{TEST_ACCOUNT_ID}",
        ),
    }.issubset(actual_user_group_relationships)

    actual_user_user_relationships = check_rels(
        neo4j_session,
        "AWSUser",
        "arn",
        "KubernetesUser",
        "id",
        "MAPS_TO",
    )
    assert {
        (
            f"arn:aws:iam::{TEST_ACCOUNT_ID}:user/template-user",
            f"{TEST_CLUSTER_NAME}/acct-user-{TEST_ACCOUNT_ID}",
        ),
    }.issubset(actual_user_user_relationships)

    assert (
        f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/TemplateSessionRole",
        f"{TEST_CLUSTER_NAME}/sso:alice@example.com",
    ) not in actual_role_user_relationships
    assert (
        f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/TemplateSessionRole",
        f"{TEST_CLUSTER_NAME}/team:alice@example.com",
    ) not in actual_role_group_relationships

    # Note: OIDC Provider nodes only contain infrastructure metadata.
    # Identity relationships (OktaUser/Group -> KubernetesUser/Group) are handled
    # by the respective data models and Okta module, not by the EKS module.


def _run_eks_sync_with_configmap_error(
    neo4j_session, status: int, caplog_level: str | None = None, caplog=None
) -> None:
    """Helper: set up AWS prereqs, mock aws-auth read to raise ApiException, run sync_eks."""
    neo4j_session.run(
        """
        MERGE (aa:AWSAccount{id: $account_id})
        ON CREATE SET aa.firstseen = timestamp()
        SET aa.lastupdated = $update_tag, aa :Tenant
        """,
        account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )
    load_kubernetes_cluster(neo4j_session, MOCK_CLUSTER_DATA, TEST_UPDATE_TAG)

    mock_k8s_client = MagicMock()
    mock_k8s_client.name = TEST_CLUSTER_NAME
    mock_k8s_client.core.read_namespaced_config_map.side_effect = ApiException(
        status=status, reason="Forbidden" if status == 403 else "Not Found"
    )

    with (
        patch(
            "cartography.intel.kubernetes.eks.get_access_entries",
            return_value=MOCK_ACCESS_ENTRIES,
        ),
        patch(
            "cartography.intel.kubernetes.eks.get_oidc_provider",
            return_value=MOCK_OIDC_PROVIDER,
        ),
    ):
        sync_eks(
            neo4j_session,
            mock_k8s_client,
            MagicMock(),
            TEST_REGION,
            TEST_UPDATE_TAG,
            TEST_CLUSTER_ID,
            TEST_CLUSTER_NAME,
        )


def test_eks_sync_skips_aws_auth_on_forbidden(neo4j_session, caplog):
    """
    When Cartography lacks `get` on the aws-auth ConfigMap, sync_eks logs a warning,
    skips legacy IAM mappings, but still ingests Access Entries and OIDC providers.
    """
    with caplog.at_level("WARNING"):
        _run_eks_sync_with_configmap_error(neo4j_session, status=403)

    assert any(
        "lacks permission to read the aws-auth ConfigMap" in record.message
        for record in caplog.records
    )

    # Access Entries users still created
    actual_users = check_nodes(neo4j_session, "KubernetesUser", ["id"])
    assert ("test-cluster/alice-access-entry",) in actual_users

    # OIDC Provider still created
    actual_oidc = check_nodes(neo4j_session, "KubernetesOIDCProvider", ["id"])
    assert (f"{TEST_CLUSTER_NAME}/oidc/okta-provider",) in actual_oidc


def test_eks_sync_skips_aws_auth_on_not_found(neo4j_session, caplog):
    """
    When the aws-auth ConfigMap does not exist (404, typical for Access Entries-only
    clusters), sync_eks logs an info message and continues with the remaining steps.
    """
    with caplog.at_level("INFO"):
        _run_eks_sync_with_configmap_error(neo4j_session, status=404)

    assert any(
        "No aws-auth ConfigMap on cluster" in record.message
        for record in caplog.records
    )

    # Access Entries still ingested
    actual_users = check_nodes(neo4j_session, "KubernetesUser", ["id"])
    assert ("test-cluster/alice-access-entry",) in actual_users
