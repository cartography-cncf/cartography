import cartography.intel.pagerduty.services
import tests.data.pagerduty.services

TEST_UPDATE_TAG = 123456789


def test_load_service_data(neo4j_session):
    service_data = tests.data.pagerduty.services.GET_SERVICES_DATA
    cartography.intel.pagerduty.services.load_service_data(
        neo4j_session,
        service_data,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "PIJ90N7",
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:PagerDutyService) RETURN n.id;
        """,
    )
    actual_nodes = {n["n.id"] for n in nodes}
    assert actual_nodes == expected_nodes


def test_load_integration_data(neo4j_session):
    integration_data = tests.data.pagerduty.services.GET_INTEGRATIONS_DATA
    cartography.intel.pagerduty.services.load_integration_data(
        neo4j_session,
        integration_data,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "PE1U9CH",
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:PagerDutyIntegration) RETURN n.id;
        """,
    )
    actual_nodes = {n["n.id"] for n in nodes}
    assert actual_nodes == expected_nodes
