import pytest

from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.namespaces import cleanup
from cartography.intel.kubernetes.namespaces import load_namespaces
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACE_IDS
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_2_NAMESPACE_IDS
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_2_NAMESPACES_DATA
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

    yield

    # Cleanup
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


def test_load_namespaces(neo4j_session, _create_test_cluster):
    # Arrange
    cluster_1_data = KUBERNETES_CLUSTER_1_NAMESPACES_DATA
    cluster_2_data = KUBERNETES_CLUSTER_2_NAMESPACES_DATA

    # Act
    load_namespaces(
        neo4j_session,
        cluster_1_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_NAMES[0],
        KUBERNETES_CLUSTER_IDS[0],
    )
    load_namespaces(
        neo4j_session,
        cluster_2_data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_NAMES[1],
        KUBERNETES_CLUSTER_IDS[1],
    )

    # Assert: Expect namespaces are loaded for both clusters
    expected_nodes = {
        (KUBERNETES_CLUSTER_1_NAMESPACE_IDS[0],),
        (KUBERNETES_CLUSTER_1_NAMESPACE_IDS[1],),
        (KUBERNETES_CLUSTER_2_NAMESPACE_IDS[0],),
        (KUBERNETES_CLUSTER_2_NAMESPACE_IDS[1],),
    }
    assert check_nodes(neo4j_session, "KubernetesNamespace", ["id"]) == expected_nodes


def test_load_namespaces_relationships(neo4j_session, _create_test_cluster):
    # Arrange
    data = KUBERNETES_CLUSTER_1_NAMESPACES_DATA

    # Act: Load namespaces for both clusters
    load_namespaces(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_NAMES[0],
        KUBERNETES_CLUSTER_IDS[0],
    )
    load_namespaces(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_NAMES[1],
        KUBERNETES_CLUSTER_IDS[1],
    )

    # Assert: Expect the relationship only exists between the cluster and its own namespaces
    expected_rels = {
        (KUBERNETES_CLUSTER_IDS[0], "kube-system"),
        (KUBERNETES_CLUSTER_IDS[0], "my-namespace"),
        (KUBERNETES_CLUSTER_IDS[1], "kube-system"),
        (KUBERNETES_CLUSTER_IDS[1], "my-namespace"),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesCluster",
            "id",
            "KubernetesNamespace",
            "name",
            "RESOURCE",
        )
        == expected_rels
    )


def test_namespace_cleanup(neo4j_session, _create_test_cluster):
    # Arrange
    data = KUBERNETES_CLUSTER_1_NAMESPACES_DATA
    load_namespaces(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_NAMES[0],
        KUBERNETES_CLUSTER_IDS[0],
    )

    # Act
    TEST_COMMON_JOB_PARAMETERS["UPDATE_TAG"] = TEST_UPDATE_TAG + 1
    TEST_COMMON_JOB_PARAMETERS["CLUSTER_ID"] = KUBERNETES_CLUSTER_IDS[0]
    cleanup(
        neo4j_session,
        TEST_COMMON_JOB_PARAMETERS,
    )

    # Assert: Expect no namespaces in the graph
    assert check_nodes(neo4j_session, "KubernetesNamespace", ["name"]) == set()
    assert (
        check_rels(
            neo4j_session,
            "KubernetesCluster",
            "id",
            "KubernetesNamespace",
            "name",
            "RESOURCE",
        )
        == set()
    )

    # Assert: Expect that the cluster was not touched by the cleanup job
    assert check_nodes(neo4j_session, "KubernetesCluster", ["id"]) == {
        (KUBERNETES_CLUSTER_IDS[0],),
        (KUBERNETES_CLUSTER_IDS[1],),
    }
