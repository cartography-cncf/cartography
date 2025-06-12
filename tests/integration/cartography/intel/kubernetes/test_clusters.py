# from cartography.intel.kubernetes.clusters import cleanup
from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


def test_load_clusters(neo4j_session):
    # Arrange
    data = KUBERNETES_CLUSTER_DATA

    # Act
    load_kubernetes_cluster(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected_nodes = {
        (KUBERNETES_CLUSTER_IDS[0],),
        (KUBERNETES_CLUSTER_IDS[1],),
    }
    assert check_nodes(neo4j_session, "KubernetesCluster", ["id"]) == expected_nodes


# cleaning up the kubernetes cluster node is currently not supported
# def test_cluster_cleanup(neo4j_session):
#     # Arrange
#     data = KUBERNETES_CLUSTER_DATA
#     load_kubernetes_cluster(
#         neo4j_session,
#         data,
#         TEST_UPDATE_TAG,
#     )

#     # Act
#     common_job_parameters = {
#         "UPDATE_TAG": TEST_UPDATE_TAG + 1,
#     }
#     cleanup(
#         neo4j_session,
#         common_job_parameters,
#     )

#     # Assert
#     assert check_nodes(neo4j_session, "KubernetesCluster", ["id"]) == set()
