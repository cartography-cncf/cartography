from cartography.intel.kubernetes.namespaces import load_namespaces
from tests.data.kubernetes.namespaces import GET_CLUSTER_DATA
from tests.data.kubernetes.namespaces import GET_NAMESPACES_DATA

TEST_UPDATE_TAG = 123456789


def test_load_namespaces(neo4j_session):
    load_namespaces(
        neo4j_session,
        GET_CLUSTER_DATA,
        GET_NAMESPACES_DATA,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {"my-cluster"}
    nodes = neo4j_session.run(
        """
        MATCH (n:KubernetesCluster) RETURN n.name
        """,
    )
    actual_nodes = {n["n.name"] for n in nodes}
    assert actual_nodes == expected_nodes

    expected_nodes = {"kube-system", "my-namespace"}
    nodes = neo4j_session.run(
        """
        MATCH (:KubernetesCluster {name: "my-cluster"})-[:HAS_NAMESPACE]->(n:KubernetesNamespace)
        RETURN n.name
        """,
    )
    actual_nodes = {n["n.name"] for n in nodes}
    assert actual_nodes == expected_nodes
