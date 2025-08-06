import pytest

from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.rbac import cleanup
from cartography.intel.kubernetes.rbac import load_cluster_role_bindings
from cartography.intel.kubernetes.rbac import load_cluster_roles
from cartography.intel.kubernetes.rbac import load_role_bindings
from cartography.intel.kubernetes.rbac import load_roles
from cartography.intel.kubernetes.rbac import load_service_accounts
from cartography.intel.kubernetes.rbac import transform_cluster_role_bindings
from cartography.intel.kubernetes.rbac import transform_cluster_roles
from cartography.intel.kubernetes.rbac import transform_role_bindings
from cartography.intel.kubernetes.rbac import transform_roles
from cartography.intel.kubernetes.rbac import transform_service_accounts
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
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_2_CLUSTER_ROLE_BINDING_IDS
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_2_CLUSTER_ROLE_BINDINGS_RAW
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_2_CLUSTER_ROLE_IDS
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_2_CLUSTER_ROLES_RAW
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_2_ROLE_BINDING_IDS
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_2_ROLE_BINDINGS_RAW
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_2_ROLE_IDS
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_2_ROLES_RAW
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_2_SERVICE_ACCOUNT_IDS
from tests.data.kubernetes.rbac import KUBERNETES_CLUSTER_2_SERVICE_ACCOUNTS_RAW
from tests.data.kubernetes.rbac import RBAC_TEST_NAMESPACES_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_COMMON_JOB_PARAMETERS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
}


@pytest.fixture
def _create_test_cluster(neo4j_session):
    # Create Test KubernetesCluster
    load_kubernetes_cluster(
        neo4j_session,
        KUBERNETES_CLUSTER_DATA,
        TEST_UPDATE_TAG,
    )

    # Create Test Namespaces that our RBAC resources will reference
    load_namespaces(
        neo4j_session,
        RBAC_TEST_NAMESPACES_DATA,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_NAMES[0],
        KUBERNETES_CLUSTER_IDS[0],
    )

    yield

    # Cleanup
    neo4j_session.run(
        """
        MATCH (k:KubernetesServiceAccount)
        DETACH DELETE k
        """,
    )
    neo4j_session.run(
        """
        MATCH (k:KubernetesRole)
        DETACH DELETE k
        """,
    )
    neo4j_session.run(
        """
        MATCH (k:KubernetesRoleBinding)
        DETACH DELETE k
        """,
    )
    neo4j_session.run(
        """
        MATCH (k:KubernetesClusterRole)
        DETACH DELETE k
        """,
    )
    neo4j_session.run(
        """
        MATCH (k:KubernetesClusterRoleBinding)
        DETACH DELETE k
        """,
    )
    neo4j_session.run(
        """
        MATCH (k:KubernetesNamespace)
        DETACH DELETE k
        """,
    )
    neo4j_session.run(
        """
        MATCH (k:KubernetesCluster)
        DETACH DELETE k
        """,
    )


def test_load_rbac_nodes(neo4j_session, _create_test_cluster):
    # Arrange: Use raw API data and transform it
    cluster_1_sa_data = transform_service_accounts(
        KUBERNETES_CLUSTER_1_SERVICE_ACCOUNTS_RAW
    )
    cluster_1_roles_data = transform_roles(KUBERNETES_CLUSTER_1_ROLES_RAW)
    cluster_1_rb_data = transform_role_bindings(KUBERNETES_CLUSTER_1_ROLE_BINDINGS_RAW)
    cluster_1_cr_data = transform_cluster_roles(KUBERNETES_CLUSTER_1_CLUSTER_ROLES_RAW)
    cluster_1_crb_data = transform_cluster_role_bindings(
        KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDINGS_RAW
    )
    cluster_2_sa_data = transform_service_accounts(
        KUBERNETES_CLUSTER_2_SERVICE_ACCOUNTS_RAW
    )
    cluster_2_roles_data = transform_roles(KUBERNETES_CLUSTER_2_ROLES_RAW)
    cluster_2_rb_data = transform_role_bindings(KUBERNETES_CLUSTER_2_ROLE_BINDINGS_RAW)
    cluster_2_cr_data = transform_cluster_roles(KUBERNETES_CLUSTER_2_CLUSTER_ROLES_RAW)
    cluster_2_crb_data = transform_cluster_role_bindings(
        KUBERNETES_CLUSTER_2_CLUSTER_ROLE_BINDINGS_RAW
    )

    # Act: Load transformed data
    load_service_accounts(
        neo4j_session,
        cluster_1_sa_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )
    load_roles(
        neo4j_session,
        cluster_1_roles_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )
    load_role_bindings(
        neo4j_session,
        cluster_1_rb_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )
    load_cluster_roles(
        neo4j_session,
        cluster_1_cr_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )
    load_cluster_role_bindings(
        neo4j_session,
        cluster_1_crb_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )
    load_service_accounts(
        neo4j_session,
        cluster_2_sa_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[1],
        KUBERNETES_CLUSTER_NAMES[1],
    )
    load_roles(
        neo4j_session,
        cluster_2_roles_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[1],
        KUBERNETES_CLUSTER_NAMES[1],
    )
    load_role_bindings(
        neo4j_session,
        cluster_2_rb_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[1],
        KUBERNETES_CLUSTER_NAMES[1],
    )
    load_cluster_roles(
        neo4j_session,
        cluster_2_cr_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[1],
        KUBERNETES_CLUSTER_NAMES[1],
    )
    load_cluster_role_bindings(
        neo4j_session,
        cluster_2_crb_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[1],
        KUBERNETES_CLUSTER_NAMES[1],
    )

    # Assert: Expect all RBAC nodes are loaded for both clusters
    expected_service_accounts = {
        (KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS[0],),
        (KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS[1],),
        (KUBERNETES_CLUSTER_2_SERVICE_ACCOUNT_IDS[0],),
    }
    assert (
        check_nodes(neo4j_session, "KubernetesServiceAccount", ["id"])
        == expected_service_accounts
    )

    expected_roles = {
        (KUBERNETES_CLUSTER_1_ROLE_IDS[0],),
        (KUBERNETES_CLUSTER_1_ROLE_IDS[1],),
        (KUBERNETES_CLUSTER_2_ROLE_IDS[0],),
    }
    assert check_nodes(neo4j_session, "KubernetesRole", ["id"]) == expected_roles

    expected_role_bindings = {
        (KUBERNETES_CLUSTER_1_ROLE_BINDING_IDS[0],),
        (KUBERNETES_CLUSTER_1_ROLE_BINDING_IDS[1],),
        (KUBERNETES_CLUSTER_2_ROLE_BINDING_IDS[0],),
    }
    assert (
        check_nodes(neo4j_session, "KubernetesRoleBinding", ["id"])
        == expected_role_bindings
    )

    expected_cluster_roles = {
        (KUBERNETES_CLUSTER_1_CLUSTER_ROLE_IDS[0],),
        (KUBERNETES_CLUSTER_1_CLUSTER_ROLE_IDS[1],),
        (KUBERNETES_CLUSTER_2_CLUSTER_ROLE_IDS[0],),
    }
    assert (
        check_nodes(neo4j_session, "KubernetesClusterRole", ["id"])
        == expected_cluster_roles
    )

    expected_cluster_role_bindings = {
        (KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDING_IDS[0],),
        (KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDING_IDS[1],),
        (KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDING_IDS[2],),
        (KUBERNETES_CLUSTER_2_CLUSTER_ROLE_BINDING_IDS[0],),
    }
    assert (
        check_nodes(neo4j_session, "KubernetesClusterRoleBinding", ["id"])
        == expected_cluster_role_bindings
    )


def test_load_rbac_relationships(neo4j_session, _create_test_cluster):
    # Arrange: Transform raw API data
    cluster_1_sa_data = transform_service_accounts(
        KUBERNETES_CLUSTER_1_SERVICE_ACCOUNTS_RAW
    )
    cluster_1_roles_data = transform_roles(KUBERNETES_CLUSTER_1_ROLES_RAW)
    cluster_1_rb_data = transform_role_bindings(KUBERNETES_CLUSTER_1_ROLE_BINDINGS_RAW)
    cluster_1_cr_data = transform_cluster_roles(KUBERNETES_CLUSTER_1_CLUSTER_ROLES_RAW)
    cluster_1_crb_data = transform_cluster_role_bindings(
        KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDINGS_RAW
    )

    # Act: Load RBAC resources for cluster 1
    load_service_accounts(
        neo4j_session,
        cluster_1_sa_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )
    load_roles(
        neo4j_session,
        cluster_1_roles_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )
    load_role_bindings(
        neo4j_session,
        cluster_1_rb_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )
    load_cluster_roles(
        neo4j_session,
        cluster_1_cr_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )
    load_cluster_role_bindings(
        neo4j_session,
        cluster_1_crb_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert: Test ServiceAccount relationships
    expected_sa_to_cluster_rels = {
        (KUBERNETES_CLUSTER_IDS[0], "demo-ns/demo-sa"),
        (KUBERNETES_CLUSTER_IDS[0], "demo-ns/another-sa"),
        (KUBERNETES_CLUSTER_IDS[0], "test-ns/test-sa"),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesCluster",
            "id",
            "KubernetesServiceAccount",
            "id",
            "RESOURCE",
        )
        == expected_sa_to_cluster_rels
    )

    # Assert: Test Cluster to Role relationships
    expected_role_to_cluster_rels = {
        (KUBERNETES_CLUSTER_IDS[0], "demo-ns/pod-reader"),
        (KUBERNETES_CLUSTER_IDS[0], "demo-ns/secret-manager"),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesCluster",
            "id",
            "KubernetesRole",
            "id",
            "RESOURCE",
        )
        == expected_role_to_cluster_rels
    )

    # Assert: Test RoleBinding to ServiceAccount relationships
    expected_rb_to_sa_rels = {
        ("demo-ns/bind-demo-sa/demo-ns/demo-sa", "demo-ns/demo-sa"),
        ("demo-ns/bind-another-sa/demo-ns/another-sa", "demo-ns/another-sa"),
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

    # Assert: Test RoleBinding to Role relationships
    expected_rb_to_role_rels = {
        ("demo-ns/bind-demo-sa/demo-ns/demo-sa", "demo-ns/pod-reader"),
        ("demo-ns/bind-another-sa/demo-ns/another-sa", "demo-ns/secret-manager"),
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

    # Assert: Test Namespace contains ServiceAccount relationships
    expected_ns_to_sa_rels = {
        ("demo-ns", "demo-ns/demo-sa"),
        ("demo-ns", "demo-ns/another-sa"),
        ("test-ns", "test-ns/test-sa"),
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

    # Assert: Test Namespace contains Role relationships
    expected_ns_to_role_rels = {
        ("demo-ns", "demo-ns/pod-reader"),
        ("demo-ns", "demo-ns/secret-manager"),
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

    # Assert: Test Namespace contains RoleBinding relationships
    expected_ns_to_rb_rels = {
        ("demo-ns", "demo-ns/bind-demo-sa/demo-ns/demo-sa"),
        ("demo-ns", "demo-ns/bind-another-sa/demo-ns/another-sa"),
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

    # Assert: Test ClusterRole relationships
    expected_cr_to_cluster_rels = {
        (KUBERNETES_CLUSTER_IDS[0], "cluster-admin"),
        (KUBERNETES_CLUSTER_IDS[0], "pod-viewer"),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesCluster",
            "id",
            "KubernetesClusterRole",
            "id",
            "RESOURCE",
        )
        == expected_cr_to_cluster_rels
    )

    # Assert: Test ClusterRoleBinding to Cluster relationships
    expected_crb_to_cluster_rels = {
        (KUBERNETES_CLUSTER_IDS[0], "admin-binding/demo-ns/demo-sa"),
        (KUBERNETES_CLUSTER_IDS[0], "viewer-binding/demo-ns/another-sa"),
        (KUBERNETES_CLUSTER_IDS[0], "viewer-binding/test-ns/test-sa"),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesCluster",
            "id",
            "KubernetesClusterRoleBinding",
            "id",
            "RESOURCE",
        )
        == expected_crb_to_cluster_rels
    )

    # Assert: Test ClusterRoleBinding to ServiceAccount relationships
    expected_crb_to_sa_rels = {
        ("admin-binding/demo-ns/demo-sa", "demo-ns/demo-sa"),
        ("viewer-binding/demo-ns/another-sa", "demo-ns/another-sa"),
        ("viewer-binding/test-ns/test-sa", "test-ns/test-sa"),
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

    # Assert: Test ClusterRoleBinding to ClusterRole relationships
    expected_crb_to_cr_rels = {
        ("admin-binding/demo-ns/demo-sa", "cluster-admin"),
        ("viewer-binding/demo-ns/another-sa", "pod-viewer"),
        ("viewer-binding/test-ns/test-sa", "pod-viewer"),
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

    # Assert: Test Namespace contains ClusterRoleBinding relationships (cross-namespace bindings)
    expected_ns_to_crb_rels = {
        ("demo-ns", "admin-binding/demo-ns/demo-sa"),
        ("demo-ns", "viewer-binding/demo-ns/another-sa"),
        ("test-ns", "viewer-binding/test-ns/test-sa"),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesNamespace",
            "name",
            "KubernetesClusterRoleBinding",
            "id",
            "CONTAINS",
        )
        == expected_ns_to_crb_rels
    )


def test_rbac_cleanup(neo4j_session, _create_test_cluster):
    # Arrange: Transform raw API data and load it
    cluster_1_sa_data = transform_service_accounts(
        KUBERNETES_CLUSTER_1_SERVICE_ACCOUNTS_RAW
    )
    cluster_1_roles_data = transform_roles(KUBERNETES_CLUSTER_1_ROLES_RAW)
    cluster_1_rb_data = transform_role_bindings(KUBERNETES_CLUSTER_1_ROLE_BINDINGS_RAW)
    cluster_1_cr_data = transform_cluster_roles(KUBERNETES_CLUSTER_1_CLUSTER_ROLES_RAW)
    cluster_1_crb_data = transform_cluster_role_bindings(
        KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDINGS_RAW
    )

    load_service_accounts(
        neo4j_session,
        cluster_1_sa_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )
    load_roles(
        neo4j_session,
        cluster_1_roles_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )
    load_role_bindings(
        neo4j_session,
        cluster_1_rb_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )
    load_cluster_roles(
        neo4j_session,
        cluster_1_cr_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )
    load_cluster_role_bindings(
        neo4j_session,
        cluster_1_crb_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )

    # Act
    TEST_COMMON_JOB_PARAMETERS["UPDATE_TAG"] = TEST_UPDATE_TAG + 1
    TEST_COMMON_JOB_PARAMETERS["CLUSTER_ID"] = KUBERNETES_CLUSTER_IDS[0]
    cleanup(
        neo4j_session,
        TEST_COMMON_JOB_PARAMETERS,
    )

    # Assert: Expect no RBAC resources in the graph
    assert check_nodes(neo4j_session, "KubernetesServiceAccount", ["id"]) == set()
    assert check_nodes(neo4j_session, "KubernetesRole", ["id"]) == set()
    assert check_nodes(neo4j_session, "KubernetesRoleBinding", ["id"]) == set()
    assert check_nodes(neo4j_session, "KubernetesClusterRole", ["id"]) == set()
    assert check_nodes(neo4j_session, "KubernetesClusterRoleBinding", ["id"]) == set()

    # Assert: Expect no RBAC relationships in the graph
    assert (
        check_rels(
            neo4j_session,
            "KubernetesCluster",
            "id",
            "KubernetesServiceAccount",
            "id",
            "RESOURCE",
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "KubernetesCluster",
            "id",
            "KubernetesRole",
            "id",
            "RESOURCE",
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "KubernetesRoleBinding",
            "id",
            "KubernetesServiceAccount",
            "id",
            "SUBJECT",
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "KubernetesNamespace",
            "name",
            "KubernetesServiceAccount",
            "id",
            "CONTAINS",
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "KubernetesNamespace",
            "name",
            "KubernetesRole",
            "id",
            "CONTAINS",
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "KubernetesNamespace",
            "name",
            "KubernetesRoleBinding",
            "id",
            "CONTAINS",
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "KubernetesCluster",
            "id",
            "KubernetesClusterRole",
            "id",
            "RESOURCE",
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "KubernetesCluster",
            "id",
            "KubernetesClusterRoleBinding",
            "id",
            "RESOURCE",
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "KubernetesClusterRoleBinding",
            "id",
            "KubernetesServiceAccount",
            "id",
            "SUBJECT",
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "KubernetesClusterRoleBinding",
            "id",
            "KubernetesClusterRole",
            "id",
            "ROLE_REF",
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "KubernetesNamespace",
            "name",
            "KubernetesClusterRoleBinding",
            "id",
            "CONTAINS",
        )
        == set()
    )

    # Assert: Expect that the clusters were not touched by the cleanup job
    assert check_nodes(neo4j_session, "KubernetesCluster", ["id"]) == {
        (KUBERNETES_CLUSTER_IDS[0],),
        (KUBERNETES_CLUSTER_IDS[1],),
    }
