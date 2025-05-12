from cartography.intel.kubernetes.pods import load_pods
from tests.data.kubernetes.pods import GET_PODS_DATA
from tests.integration.cartography.intel.kubernetes.test_namespaces import (
    test_load_namespaces,
)

TEST_UPDATE_TAG = 123456789


def test_load_pods(neo4j_session):
    test_load_namespaces(neo4j_session)
    load_pods(neo4j_session, GET_PODS_DATA, TEST_UPDATE_TAG)

    expected_nodes = {"my-pod", "my-service-pod"}
    nodes = neo4j_session.run(
        """
        MATCH (n:KubernetesPod) RETURN n.name
        """,
    )
    actual_nodes = {n["n.name"] for n in nodes}
    assert actual_nodes == expected_nodes

    expected_nodes = {"my-pod-container"}
    nodes = neo4j_session.run(
        """
        MATCH (:KubernetesPod {name: "my-pod"})-[:HAS_CONTAINER]->(n:KubernetesContainer)
        RETURN n.name
        """,
    )
    actual_nodes = {n["n.name"] for n in nodes}
    assert actual_nodes == expected_nodes
