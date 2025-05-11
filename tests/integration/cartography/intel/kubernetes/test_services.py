from cartography.intel.kubernetes.services import load_services
from tests.data.kubernetes.services import GET_SERVICES_DATA
from tests.integration.cartography.intel.kubernetes.test_namespaces import (
    test_load_namespaces,
)
from tests.integration.cartography.intel.kubernetes.test_pods import test_load_pods

TEST_UPDATE_TAG = 123456789


def test_load_services(neo4j_session):
    test_load_namespaces(neo4j_session)
    test_load_pods(neo4j_session)
    load_services(neo4j_session, GET_SERVICES_DATA, TEST_UPDATE_TAG)

    expected_nodes = {"my-service"}
    nodes = neo4j_session.run(
        """
        MATCH (n:KubernetesService) RETURN n.name
        """,
    )
    actual_nodes = {n["n.name"] for n in nodes}
    assert actual_nodes == expected_nodes

    expected_nodes = {"my-service-pod"}
    nodes = neo4j_session.run(
        """
        MATCH (:KubernetesService)-[:SERVES_POD]->(n:KubernetesPod)
        RETURN n.name
        """,
    )
    actual_nodes = {n["n.name"] for n in nodes}
    assert actual_nodes == expected_nodes
