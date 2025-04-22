from cartography.intel.kubernetes.namespaces import cleanup
from cartography.intel.kubernetes.namespaces import load_namespaces
from tests.data.kubernetes.namespaces import KUBERNETES_NAMESPACES_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "kubernetes-cluster-id"
TEST_COMMON_JOB_PARAMETERS = {
    'UPDATE_TAG': TEST_UPDATE_TAG,
    'CLUSTER_ID': TEST_CLUSTER_ID,
}


def _create_test_cluster(neo4j_session):
    # Create Test KubernetesCluster
    neo4j_session.run(
        """
        MERGE (c:KubernetesCluster{id: $cluster_id})
        ON CREATE SET c.firstseen = timestamp()
        SET c.lastupdated = $update_tag
        """,
        cluster_id=TEST_CLUSTER_ID,
        update_tag=TEST_UPDATE_TAG,
    )


def test_load_namespaces(neo4j_session):
    # Arrange
    data = KUBERNETES_NAMESPACES_DATA

    # Act
    load_namespaces(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
        TEST_COMMON_JOB_PARAMETERS,
    )

    expected_nodes = {
        ("kube-system",),
        ("my-namespace",),
    }
    assert check_nodes(neo4j_session, 'KubernetesNamespace', ['name']) == expected_nodes


def test_load_namespaces_relationships(neo4j_session):
    # Arrange
    data = KUBERNETES_NAMESPACES_DATA
    _create_test_cluster(neo4j_session)

    # Act
    load_namespaces(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
        TEST_COMMON_JOB_PARAMETERS,
    )

    expected_rels = {
        (TEST_CLUSTER_ID, 'kube-system'),
        (TEST_CLUSTER_ID, 'my-namespace'),
    }
    assert check_rels(
        neo4j_session,
        'KubernetesCluster',
        'id',
        'KubernetesNamespace',
        'name',
        'RESOURCE',
    ) == expected_rels


def test_namespace_cleanup(neo4j_session):
    # Arrange
    data = KUBERNETES_NAMESPACES_DATA
    _create_test_cluster(neo4j_session)
    load_namespaces(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
        TEST_COMMON_JOB_PARAMETERS,
    )

    # Act
    TEST_COMMON_JOB_PARAMETERS['UPDATE_TAG'] = TEST_UPDATE_TAG + 1
    cleanup(
        neo4j_session,
        TEST_COMMON_JOB_PARAMETERS,
    )

    # Assert: Expect no namespaces in the graph
    assert check_nodes(neo4j_session, 'KubernetesNamespace', ['name']) == set()
    assert check_rels(
        neo4j_session,
        'KubernetesCluster',
        'id',
        'KubernetesNamespace',
        'name',
        'RESOURCE',
    ) == set()

    # Assert: Expect that the cluster was not touched by the cleanup job
    assert check_nodes(neo4j_session, 'KubernetesCluster', ['id']) == {
        (TEST_CLUSTER_ID,),
    }
