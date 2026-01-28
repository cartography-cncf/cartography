from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.pagerduty.teams
import tests.data.pagerduty.teams
from tests.integration.cartography.intel.pagerduty.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789

GET_TEAM_MEMBERS_DATA = [
    {"team": "PQ9K7I8", "user": "PXPGF42", "role": "manager"},
    {"team": "PQ9K7I8", "user": "PAM4FGS", "role": "responder"},
]


def _ensure_local_neo4j_has_test_teams(neo4j_session):
    cartography.intel.pagerduty.teams.load_team_data(
        neo4j_session,
        tests.data.pagerduty.teams.GET_TEAMS_DATA,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.pagerduty.teams,
    "get_team_members",
    return_value=GET_TEAM_MEMBERS_DATA,
)
@patch.object(
    cartography.intel.pagerduty.teams,
    "get_teams",
    return_value=tests.data.pagerduty.teams.GET_TEAMS_DATA,
)
def test_load_team_data(mock_teams, mock_members, neo4j_session):
    # Arrange
    api_session = Mock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}
    _ensure_local_neo4j_has_test_users(neo4j_session)

    # Act
    cartography.intel.pagerduty.teams.sync_teams(
        neo4j_session, TEST_UPDATE_TAG, api_session, common_job_parameters
    )

    # Assert nodes exists
    expected_nodes = {("PQ9K7I8", "Engineering")}
    assert check_nodes(neo4j_session, "PagerDutyTeam", ["id", "name"]) == expected_nodes

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

    # Check that the role property is set on the relationship
    result = neo4j_session.run(
        """
        MATCH (u:PagerDutyUser)-[r:MEMBER_OF]->(t:PagerDutyTeam)
        RETURN u.id as user_id, t.id as team_id, r.role as role
        ORDER BY u.id
        """
    )
    roles = {
        (record["user_id"], record["team_id"], record["role"]) for record in result
    }
    expected_roles = {
        ("PAM4FGS", "PQ9K7I8", "responder"),
        ("PXPGF42", "PQ9K7I8", "manager"),
    }
    assert roles == expected_roles
