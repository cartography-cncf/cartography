from unittest.mock import patch

import cartography.intel.pagerduty.services
import cartography.intel.pagerduty.teams
import cartography.intel.pagerduty.vendors
from tests.data.pagerduty.services import GET_INTEGRATIONS_DATA
from tests.data.pagerduty.services import GET_SERVICES_DATA
from tests.data.pagerduty.teams import GET_TEAMS_DATA
from tests.data.pagerduty.vendors import GET_VENDORS_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.pagerduty.vendors,
    "get_vendors",
    return_value=GET_VENDORS_DATA,
)
@patch.object(
    cartography.intel.pagerduty.teams,
    "get_team_members",
    return_value=[],
)
@patch.object(
    cartography.intel.pagerduty.teams,
    "get_teams",
    return_value=GET_TEAMS_DATA,
)
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
def test_sync_services(
    mock_get_services,
    mock_get_integrations,
    mock_get_teams,
    mock_get_team_members,
    mock_get_vendors,
    neo4j_session,
):
    """
    Test that services and integrations sync correctly and create proper nodes and relationships
    """
    # Mock PD session (not actually used due to mocks)
    mock_pd_session = None

    # First sync teams and vendors so they exist for the relationships
    cartography.intel.pagerduty.teams.sync_teams(
        neo4j_session,
        TEST_UPDATE_TAG,
        mock_pd_session,
    )
    cartography.intel.pagerduty.vendors.sync_vendors(
        neo4j_session,
        TEST_UPDATE_TAG,
        mock_pd_session,
    )

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

    # Check relationships between teams and services
    expected_team_service_rels = {
        ("PQ9K7I8", "PIJ90N7"),
    }
    assert (
        check_rels(
            neo4j_session,
            "PagerDutyTeam",
            "id",
            "PagerDutyService",
            "id",
            "ASSOCIATED_WITH",
            rel_direction_right=True,
        )
        == expected_team_service_rels
    )

    # Check relationships between services and integrations
    expected_service_integration_rels = {
        ("PIJ90N7", "PE1U9CH"),
    }
    assert (
        check_rels(
            neo4j_session,
            "PagerDutyService",
            "id",
            "PagerDutyIntegration",
            "id",
            "HAS_INTEGRATION",
            rel_direction_right=True,
        )
        == expected_service_integration_rels
    )

    # Check relationships between integrations and vendors
    expected_integration_vendor_rels = {
        ("PE1U9CH", "PZQ6AUS"),
    }
    assert (
        check_rels(
            neo4j_session,
            "PagerDutyIntegration",
            "id",
            "PagerDutyVendor",
            "id",
            "HAS_VENDOR",
            rel_direction_right=True,
        )
        == expected_integration_vendor_rels
    )
