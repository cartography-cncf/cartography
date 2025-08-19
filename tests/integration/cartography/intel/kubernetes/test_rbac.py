from unittest.mock import Mock
from unittest.mock import patch

import pytest

from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.rbac import sync_kubernetes_rbac
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDING_IDS
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDINGS_RAW
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_CLUSTER_ROLE_IDS
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_CLUSTER_ROLES_RAW
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_ROLE_BINDING_IDS
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_ROLE_BINDINGS_RAW
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_ROLE_IDS
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_ROLES_RAW
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_1_SERVICE_ACCOUNTS_RAW
from tests.data.kubernetes.rbac import RBAC_TEST_NAMESPACES_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@pytest.fixture
def mock_k8s_client():
    """Mock K8sClient for end-to-end testing."""
    client = Mock()
    client.name = KUBERNETES_CLUSTER_NAMES[0]
    return client


@patch("cartography.intel.kubernetes.rbac.get_service_accounts")
@patch("cartography.intel.kubernetes.rbac.get_roles")
@patch("cartography.intel.kubernetes.rbac.get_role_bindings")
@patch("cartography.intel.kubernetes.rbac.get_cluster_roles")
@patch("cartography.intel.kubernetes.rbac.get_cluster_role_bindings")
def test_sync_kubernetes_rbac_end_to_end(
    mock_get_cluster_role_bindings,
    mock_get_cluster_roles,
    mock_get_role_bindings,
    mock_get_roles,
    mock_get_service_accounts,
    neo4j_session,
    mock_k8s_client,
):

    # Arrange: Create prerequisite cluster and namespace nodes that RBAC resources will reference
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

    # Arrange: Configure mock return values
    mock_get_service_accounts.return_value = KUBERNETES_CLUSTER_1_SERVICE_ACCOUNTS_RAW
    mock_get_roles.return_value = KUBERNETES_CLUSTER_1_ROLES_RAW
    mock_get_role_bindings.return_value = KUBERNETES_CLUSTER_1_ROLE_BINDINGS_RAW
    mock_get_cluster_roles.return_value = KUBERNETES_CLUSTER_1_CLUSTER_ROLES_RAW
    mock_get_cluster_role_bindings.return_value = (
        KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDINGS_RAW
    )

    # Act: Run the actual end-to-end sync function
    sync_kubernetes_rbac(
        neo4j_session,
        mock_k8s_client,
        TEST_UPDATE_TAG,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0],
        },
    )

    # Assert: Verify all RBAC nodes were loaded correctly
    expected_service_accounts = {
        (KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS[0],),
        (KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS[1],),
        (KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS[2],),
    }
    assert (
        check_nodes(neo4j_session, "KubernetesServiceAccount", ["id"])
        == expected_service_accounts
    )

    expected_roles = {
        (KUBERNETES_CLUSTER_1_ROLE_IDS[0],),
        (KUBERNETES_CLUSTER_1_ROLE_IDS[1],),
    }
    assert check_nodes(neo4j_session, "KubernetesRole", ["id"]) == expected_roles

    expected_role_bindings = {
        (KUBERNETES_CLUSTER_1_ROLE_BINDING_IDS[0],),
        (KUBERNETES_CLUSTER_1_ROLE_BINDING_IDS[1],),
    }
    assert (
        check_nodes(neo4j_session, "KubernetesRoleBinding", ["id"])
        == expected_role_bindings
    )

    expected_cluster_roles = {
        (KUBERNETES_CLUSTER_1_CLUSTER_ROLE_IDS[0],),
        (KUBERNETES_CLUSTER_1_CLUSTER_ROLE_IDS[1],),
    }
    assert (
        check_nodes(neo4j_session, "KubernetesClusterRole", ["id"])
        == expected_cluster_roles
    )

    expected_cluster_role_bindings = {
        (KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDING_IDS[0],),
        (KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDING_IDS[1],),
    }
    assert (
        check_nodes(neo4j_session, "KubernetesClusterRoleBinding", ["id"])
        == expected_cluster_role_bindings
    )

    # Assert: Verify RBAC authorization relationships (ROLE_REF)
    expected_rb_to_role_rels = {
        (KUBERNETES_CLUSTER_1_ROLE_BINDING_IDS[0], KUBERNETES_CLUSTER_1_ROLE_IDS[0]),
        (KUBERNETES_CLUSTER_1_ROLE_BINDING_IDS[1], KUBERNETES_CLUSTER_1_ROLE_IDS[1]),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesRoleBinding",
            "id",
            "KubernetesRole",
            "id",
            "ROLE_REF",
        )
        == expected_rb_to_role_rels
    )

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
    assert (
        check_rels(
            neo4j_session,
            "KubernetesClusterRoleBinding",
            "id",
            "KubernetesClusterRole",
            "id",
            "ROLE_REF",
        )
        == expected_crb_to_cr_rels
    )

    # Assert: Verify all namespace CONTAINS relationships
    expected_ns_to_sa_rels = {
        ("demo-ns", KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS[0]),
        ("demo-ns", KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS[1]),
        ("test-ns", KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS[2]),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesNamespace",
            "name",
            "KubernetesServiceAccount",
            "id",
            "CONTAINS",
        )
        == expected_ns_to_sa_rels
    )

    expected_ns_to_role_rels = {
        ("demo-ns", KUBERNETES_CLUSTER_1_ROLE_IDS[0]),
        ("demo-ns", KUBERNETES_CLUSTER_1_ROLE_IDS[1]),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesNamespace",
            "name",
            "KubernetesRole",
            "id",
            "CONTAINS",
        )
        == expected_ns_to_role_rels
    )

    expected_ns_to_rb_rels = {
        ("demo-ns", KUBERNETES_CLUSTER_1_ROLE_BINDING_IDS[0]),
        ("demo-ns", KUBERNETES_CLUSTER_1_ROLE_BINDING_IDS[1]),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesNamespace",
            "name",
            "KubernetesRoleBinding",
            "id",
            "CONTAINS",
        )
        == expected_ns_to_rb_rels
    )

    # Assert: Verify SUBJECT relationships (RoleBinding/ClusterRoleBinding to ServiceAccount)
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
    assert (
        check_rels(
            neo4j_session,
            "KubernetesRoleBinding",
            "id",
            "KubernetesServiceAccount",
            "id",
            "SUBJECT",
        )
        == expected_rb_to_sa_rels
    )

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
    assert (
        check_rels(
            neo4j_session,
            "KubernetesClusterRoleBinding",
            "id",
            "KubernetesServiceAccount",
            "id",
            "SUBJECT",
        )
        == expected_crb_to_sa_rels
    )
