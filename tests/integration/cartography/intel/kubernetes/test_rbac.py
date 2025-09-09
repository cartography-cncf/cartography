from unittest.mock import Mock
from unittest.mock import patch

from cartography.intel.kubernetes import rbac
from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.rbac import sync_kubernetes_rbac
from cartography.intel.okta.groups import _load_okta_groups
from cartography.intel.okta.organization import create_okta_organization
from cartography.intel.okta.users import _load_okta_users
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDING_IDS
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDINGS_RAW
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_CLUSTER_ROLE_IDS
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_CLUSTER_ROLES_RAW
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_GROUP_IDS
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_ROLE_BINDING_IDS
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_ROLE_BINDINGS_RAW
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_ROLE_IDS
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_ROLES_RAW
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_SERVICE_ACCOUNTS_RAW
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_USER_IDS
from tests.data.kubernetes.rbac import MOCK_OKTA_GROUPS
from tests.data.kubernetes.rbac import MOCK_OKTA_USERS
from tests.data.kubernetes.rbac import RBAC_TEST_NAMESPACES_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_OKTA_ORG_ID = "test-okta-org"
TEST_COMMON_JOB_PARAMETERS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
}


@patch.object(rbac, "get_cluster_role_bindings")
@patch.object(rbac, "get_cluster_roles")
@patch.object(rbac, "get_role_bindings")
@patch.object(rbac, "get_roles")
@patch.object(rbac, "get_service_accounts")
def test_sync_rbac_end_to_end(
    mock_get_service_accounts,
    mock_get_roles,
    mock_get_role_bindings,
    mock_get_cluster_roles,
    mock_get_cluster_role_bindings,
    neo4j_session,
):
    """
    Test the complete end-to-end RBAC sync flow.
    """
    # Arrange: Mock all the get_* functions with test data
    mock_get_service_accounts.return_value = KUBERNETES_CLUSTER_1_SERVICE_ACCOUNTS_RAW
    mock_get_roles.return_value = KUBERNETES_CLUSTER_1_ROLES_RAW
    mock_get_role_bindings.return_value = KUBERNETES_CLUSTER_1_ROLE_BINDINGS_RAW
    mock_get_cluster_roles.return_value = KUBERNETES_CLUSTER_1_CLUSTER_ROLES_RAW
    mock_get_cluster_role_bindings.return_value = (
        KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDINGS_RAW
    )

    # Create a mock K8s client
    mock_client = Mock()
    mock_client.name = KUBERNETES_CLUSTER_NAMES[0]  # "my-cluster-1"

    # Define common job parameters
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0],
    }

    # Create test cluster and namespaces that RBAC resources will reference
    load_kubernetes_cluster(
        neo4j_session,
        KUBERNETES_CLUSTER_DATA,
        TEST_UPDATE_TAG,
    )
    load_namespaces(
        neo4j_session,
        RBAC_TEST_NAMESPACES_DATA,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_NAMES[0],
        KUBERNETES_CLUSTER_IDS[0],
    )

    # Load Okta users and groups for identity mapping tests
    create_okta_organization(neo4j_session, TEST_OKTA_ORG_ID, TEST_UPDATE_TAG)
    _load_okta_users(neo4j_session, TEST_OKTA_ORG_ID, MOCK_OKTA_USERS, TEST_UPDATE_TAG)
    _load_okta_groups(
        neo4j_session, TEST_OKTA_ORG_ID, MOCK_OKTA_GROUPS, TEST_UPDATE_TAG
    )

    # Act: Run the complete sync
    sync_kubernetes_rbac(
        session=neo4j_session,
        client=mock_client,
        update_tag=TEST_UPDATE_TAG,
        common_job_parameters=common_job_parameters,
    )

    # Assert: Verify all mocked functions were called
    mock_get_service_accounts.assert_called_once_with(mock_client)
    mock_get_roles.assert_called_once_with(mock_client)
    mock_get_role_bindings.assert_called_once_with(mock_client)
    mock_get_cluster_roles.assert_called_once_with(mock_client)
    mock_get_cluster_role_bindings.assert_called_once_with(mock_client)

    # Assert: Verify ServiceAccount nodes were created with cluster-scoped IDs
    expected_service_accounts = {
        (
            KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS[0],
        ),  # "my-cluster-1/demo-ns/demo-sa"
        (
            KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS[1],
        ),  # "my-cluster-1/demo-ns/another-sa"
        (
            KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS[2],
        ),  # "my-cluster-1/test-ns/test-sa"
    }
    actual_service_accounts = check_nodes(
        neo4j_session, "KubernetesServiceAccount", ["id"]
    )
    assert expected_service_accounts.issubset(actual_service_accounts)

    # Assert: Verify Role nodes were created with cluster-scoped IDs
    expected_roles = {
        (KUBERNETES_CLUSTER_1_ROLE_IDS[0],),  # "my-cluster-1/demo-ns/pod-reader"
        (KUBERNETES_CLUSTER_1_ROLE_IDS[1],),  # "my-cluster-1/demo-ns/secret-manager"
    }
    actual_roles = check_nodes(neo4j_session, "KubernetesRole", ["id"])
    assert expected_roles.issubset(actual_roles)

    # Assert: Verify RoleBinding nodes were created with cluster-scoped IDs
    expected_role_bindings = {
        (
            KUBERNETES_CLUSTER_1_ROLE_BINDING_IDS[0],
        ),  # "my-cluster-1/demo-ns/bind-demo-sa"
        (
            KUBERNETES_CLUSTER_1_ROLE_BINDING_IDS[1],
        ),  # "my-cluster-1/demo-ns/bind-another-sa"
    }
    actual_role_bindings = check_nodes(neo4j_session, "KubernetesRoleBinding", ["id"])
    assert expected_role_bindings.issubset(actual_role_bindings)

    # Assert: Verify ClusterRole nodes were created with cluster-scoped IDs
    expected_cluster_roles = {
        (KUBERNETES_CLUSTER_1_CLUSTER_ROLE_IDS[0],),  # "my-cluster-1/cluster-admin"
        (KUBERNETES_CLUSTER_1_CLUSTER_ROLE_IDS[1],),  # "my-cluster-1/pod-viewer"
    }
    actual_cluster_roles = check_nodes(neo4j_session, "KubernetesClusterRole", ["id"])
    assert expected_cluster_roles.issubset(actual_cluster_roles)

    # Assert: Verify ClusterRoleBinding nodes were created with cluster-scoped IDs
    expected_cluster_role_bindings = {
        (
            KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDING_IDS[0],
        ),  # "my-cluster-1/admin-binding"
        (
            KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDING_IDS[1],
        ),  # "my-cluster-1/viewer-binding"
    }
    actual_cluster_role_bindings = check_nodes(
        neo4j_session, "KubernetesClusterRoleBinding", ["id"]
    )
    assert expected_cluster_role_bindings.issubset(actual_cluster_role_bindings)

    # Assert: Verify User nodes were created with cluster-scoped IDs (OIDC functionality)
    expected_users = {
        (KUBERNETES_CLUSTER_1_USER_IDS[0],),  # "my-cluster-1/admin@company.com"
        (KUBERNETES_CLUSTER_1_USER_IDS[1],),  # "my-cluster-1/john.doe@company.com"
    }
    actual_users = check_nodes(neo4j_session, "KubernetesUser", ["id"])
    assert expected_users.issubset(actual_users)

    # Assert: Verify Group nodes were created with cluster-scoped IDs (OIDC functionality)
    expected_groups = {
        (KUBERNETES_CLUSTER_1_GROUP_IDS[0],),  # "my-cluster-1/admins"
        (KUBERNETES_CLUSTER_1_GROUP_IDS[1],),  # "my-cluster-1/developers"
    }
    actual_groups = check_nodes(neo4j_session, "KubernetesGroup", ["id"])
    assert expected_groups.issubset(actual_groups)

    # Assert: Verify ServiceAccount to Namespace relationships
    expected_sa_to_ns_rels = {
        ("demo-ns-uid-12345", KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS[0]),
        ("demo-ns-uid-12345", KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS[1]),
        ("test-ns-uid-67890", KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS[2]),
    }
    actual_sa_to_ns_rels = check_rels(
        neo4j_session,
        "KubernetesNamespace",
        "id",
        "KubernetesServiceAccount",
        "id",
        "CONTAINS",
    )
    assert expected_sa_to_ns_rels.issubset(actual_sa_to_ns_rels)

    # Assert: Verify RoleBinding to ServiceAccount relationships
    expected_rb_to_sa_rels = {
        (
            KUBERNETES_CLUSTER_1_ROLE_BINDING_IDS[0],
            KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS[0],
        ),
        (
            KUBERNETES_CLUSTER_1_ROLE_BINDING_IDS[1],
            KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS[1],
        ),
    }
    actual_rb_to_sa_rels = check_rels(
        neo4j_session,
        "KubernetesRoleBinding",
        "id",
        "KubernetesServiceAccount",
        "id",
        "SUBJECT",
    )
    assert expected_rb_to_sa_rels.issubset(actual_rb_to_sa_rels)

    # Assert: Verify RoleBinding to Role relationships
    expected_rb_to_role_rels = {
        (KUBERNETES_CLUSTER_1_ROLE_BINDING_IDS[0], KUBERNETES_CLUSTER_1_ROLE_IDS[0]),
        (KUBERNETES_CLUSTER_1_ROLE_BINDING_IDS[1], KUBERNETES_CLUSTER_1_ROLE_IDS[1]),
    }
    actual_rb_to_role_rels = check_rels(
        neo4j_session,
        "KubernetesRoleBinding",
        "id",
        "KubernetesRole",
        "id",
        "ROLE_REF",
    )
    assert expected_rb_to_role_rels.issubset(actual_rb_to_role_rels)

    # Assert: Verify ClusterRoleBinding to ServiceAccount relationships
    expected_crb_to_sa_rels = {
        (
            KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDING_IDS[0],
            KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS[0],
        ),
        (
            KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDING_IDS[1],
            KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS[1],
        ),
        (
            KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDING_IDS[1],
            KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS[2],
        ),
    }
    actual_crb_to_sa_rels = check_rels(
        neo4j_session,
        "KubernetesClusterRoleBinding",
        "id",
        "KubernetesServiceAccount",
        "id",
        "SUBJECT",
    )
    assert expected_crb_to_sa_rels.issubset(actual_crb_to_sa_rels)

    # Assert: Verify ClusterRoleBinding to ClusterRole relationships
    expected_crb_to_cr_rels = {
        (
            KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDING_IDS[0],
            KUBERNETES_CLUSTER_1_CLUSTER_ROLE_IDS[0],
        ),
        (
            KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDING_IDS[1],
            KUBERNETES_CLUSTER_1_CLUSTER_ROLE_IDS[1],
        ),
    }
    actual_crb_to_cr_rels = check_rels(
        neo4j_session,
        "KubernetesClusterRoleBinding",
        "id",
        "KubernetesClusterRole",
        "id",
        "ROLE_REF",
    )
    assert expected_crb_to_cr_rels.issubset(actual_crb_to_cr_rels)

    # Assert: Verify RoleBinding to User relationships (OIDC functionality)
    expected_rb_to_user_rels = {
        (KUBERNETES_CLUSTER_1_ROLE_BINDING_IDS[0], KUBERNETES_CLUSTER_1_USER_IDS[1]),
    }
    actual_rb_to_user_rels = check_rels(
        neo4j_session,
        "KubernetesRoleBinding",
        "id",
        "KubernetesUser",
        "id",
        "SUBJECT",
    )
    assert expected_rb_to_user_rels.issubset(actual_rb_to_user_rels)

    # Assert: Verify ClusterRoleBinding to User relationships (OIDC functionality)
    expected_crb_to_user_rels = {
        (
            KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDING_IDS[0],
            "my-cluster-1/admin@company.com",
        ),
    }
    actual_crb_to_user_rels = check_rels(
        neo4j_session,
        "KubernetesClusterRoleBinding",
        "id",
        "KubernetesUser",
        "id",
        "SUBJECT",
    )
    assert expected_crb_to_user_rels.issubset(actual_crb_to_user_rels)

    # Assert: Verify RoleBinding to Group relationships (OIDC functionality)
    expected_rb_to_group_rels = {
        (KUBERNETES_CLUSTER_1_ROLE_BINDING_IDS[0], "my-cluster-1/developers"),
    }
    actual_rb_to_group_rels = check_rels(
        neo4j_session,
        "KubernetesRoleBinding",
        "id",
        "KubernetesGroup",
        "id",
        "SUBJECT",
    )
    assert expected_rb_to_group_rels.issubset(actual_rb_to_group_rels)

    # Assert: Verify ClusterRoleBinding to Group relationships (OIDC functionality)
    expected_crb_to_group_rels = {
        (KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDING_IDS[0], "my-cluster-1/admins"),
    }
    actual_crb_to_group_rels = check_rels(
        neo4j_session,
        "KubernetesClusterRoleBinding",
        "id",
        "KubernetesGroup",
        "id",
        "SUBJECT",
    )
    assert expected_crb_to_group_rels.issubset(actual_crb_to_group_rels)

    # Assert: Verify Okta User to Kubernetes User identity mapping relationships
    expected_okta_user_to_k8s_user_rels = {
        (
            "john.doe@company.com",
            KUBERNETES_CLUSTER_1_USER_IDS[1],
        ),  # OktaUser.email -> KubernetesUser.name
        ("admin@company.com", KUBERNETES_CLUSTER_1_USER_IDS[0]),
    }
    actual_okta_user_to_k8s_user_rels = check_rels(
        neo4j_session,
        "OktaUser",
        "email",
        "KubernetesUser",
        "id",
        "MAPS_TO",
    )
    assert expected_okta_user_to_k8s_user_rels.issubset(
        actual_okta_user_to_k8s_user_rels
    )

    # Assert: Verify Okta Group to Kubernetes Group identity mapping relationships
    expected_okta_group_to_k8s_group_rels = {
        (
            "developers",
            "my-cluster-1/developers",
        ),  # OktaGroup.name -> KubernetesGroup.name
        ("admins", "my-cluster-1/admins"),
    }
    actual_okta_group_to_k8s_group_rels = check_rels(
        neo4j_session,
        "OktaGroup",
        "name",
        "KubernetesGroup",
        "id",
        "MAPS_TO",
    )
    assert expected_okta_group_to_k8s_group_rels.issubset(
        actual_okta_group_to_k8s_group_rels
    )
