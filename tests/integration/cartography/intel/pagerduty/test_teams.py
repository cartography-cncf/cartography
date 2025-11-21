from unittest.mock import patch

import cartography.intel.pagerduty.teams
from tests.data.pagerduty.teams import GET_TEAMS_DATA
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


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
def test_sync_teams(mock_get_teams, mock_get_team_members, neo4j_session):
    """
    Test that teams sync correctly and create proper nodes
    """
    # Mock PD session (not actually used due to mocks)
    mock_pd_session = None

    # Act - Call the sync function
    cartography.intel.pagerduty.teams.sync_teams(
        neo4j_session,
        TEST_UPDATE_TAG,
        mock_pd_session,
    )

    # Assert - Use check_nodes() instead of raw Neo4j queries
    expected_nodes = {
        ("PQ9K7I8",),
    }
    assert check_nodes(neo4j_session, "PagerDutyTeam", ["id"]) == expected_nodes
