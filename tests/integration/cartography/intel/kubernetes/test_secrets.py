from cartography.intel.kubernetes.secrets import load_secrets
from tests.data.kubernetes.secrets import GET_SECRETS_DATA
from tests.integration.cartography.intel.kubernetes.test_namespaces import (
    test_load_namespaces,
)

TEST_UPDATE_TAG = 123456789


def test_load_secrets(neo4j_session):
    test_load_namespaces(neo4j_session)
    load_secrets(neo4j_session, GET_SECRETS_DATA, TEST_UPDATE_TAG)

    expected_nodes = {"my-secret"}
    nodes = neo4j_session.run(
        """
        MATCH (n:KubernetesSecret) RETURN n.name
        """,
    )
    actual_nodes = {n["n.name"] for n in nodes}
    assert actual_nodes == expected_nodes
