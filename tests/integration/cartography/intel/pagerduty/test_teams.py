import cartography.intel.pagerduty.teams
import tests.data.pagerduty.teams

TEST_UPDATE_TAG = 123456789


def test_load_team_data(neo4j_session):
    team_data = tests.data.pagerduty.teams.GET_TEAMS_DATA
    cartography.intel.pagerduty.teams.load_team_data(
        neo4j_session,
        team_data,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "PQ9K7I8",
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:PagerDutyTeam) RETURN n.id;
        """,
    )
    actual_nodes = {n["n.id"] for n in nodes}
    assert actual_nodes == expected_nodes
