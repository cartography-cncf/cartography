from unittest.mock import patch

import cartography.intel.pagerduty.services
from tests.data.pagerduty.services import GET_INTEGRATIONS_DATA
from tests.data.pagerduty.services import GET_SERVICES_DATA
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.pagerduty.services,
    "get_integrations",
    return_value=GET_INTEGRATIONS_DATA,
)
@patch.object(
    cartography.intel.pagerduty.services,
    "get_services",
    return_value=GET_SERVICES_DATA,
)
def test_sync_services(mock_get_services, mock_get_integrations, neo4j_session):
    """
    Test that services and integrations sync correctly and create proper nodes
    """
    # Mock PD session (not actually used due to mocks)
    mock_pd_session = None

    # Act - Call the sync function
    cartography.intel.pagerduty.services.sync_services(
        neo4j_session,
        TEST_UPDATE_TAG,
        mock_pd_session,
    )

    # Assert - Use check_nodes() instead of raw Neo4j queries
    # Check services
    expected_service_nodes = {
        ("PIJ90N7",),
    }
    assert (
        check_nodes(neo4j_session, "PagerDutyService", ["id"]) == expected_service_nodes
    )

    # Check integrations
    expected_integration_nodes = {
        ("PE1U9CH",),
    }
    assert (
        check_nodes(neo4j_session, "PagerDutyIntegration", ["id"])
        == expected_integration_nodes
    )
