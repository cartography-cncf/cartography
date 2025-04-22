from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_ID
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
        (KUBERNETES_CLUSTER_ID,),
    }
    assert check_nodes(neo4j_session, 'KubernetesCluster', ['id']) == expected_nodes
