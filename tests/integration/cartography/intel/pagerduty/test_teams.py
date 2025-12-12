from unittest.mock import patch

import cartography.intel.pagerduty.teams
import cartography.intel.pagerduty.users
from tests.data.pagerduty.teams import GET_TEAMS_DATA
from tests.data.pagerduty.users import GET_USERS_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789

GET_TEAM_MEMBERS_DATA = [
    {"team": "PQ9K7I8", "user": "PXPGF42", "role": "manager"},
    {"team": "PQ9K7I8", "user": "PAM4FGS", "role": "responder"},
]


@patch.object(
    cartography.intel.pagerduty.users,
    "get_users",
    return_value=GET_USERS_DATA,
)
@patch.object(
    cartography.intel.pagerduty.teams,
    "get_team_members",
    return_value=GET_TEAM_MEMBERS_DATA,
)
@patch.object(
    cartography.intel.pagerduty.teams,
    "get_teams",
    return_value=GET_TEAMS_DATA,
)
def test_sync_teams(
    mock_get_teams, mock_get_team_members, mock_get_users, neo4j_session
):
    """
    Test that teams sync correctly and create proper nodes and relationships
    """
    # Mock PD session (not actually used due to mocks)
    mock_pd_session = None

    # First sync users so they exist for the relationship
    cartography.intel.pagerduty.users.sync_users(
        neo4j_session,
        TEST_UPDATE_TAG,
        mock_pd_session,
    )

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

    # Check relationships between users and teams
    expected_rels = {
        ("PXPGF42", "PQ9K7I8"),
        ("PAM4FGS", "PQ9K7I8"),
    }
    assert (
        check_rels(
            neo4j_session,
            "PagerDutyUser",
            "id",
            "PagerDutyTeam",
            "id",
            "MEMBER_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )
