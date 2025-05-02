import cartography.intel.pagerduty.users
import tests.data.pagerduty.users

TEST_UPDATE_TAG = 123456789


def test_load_user_data(neo4j_session):
    user_data = tests.data.pagerduty.users.GET_USERS_DATA
    cartography.intel.pagerduty.users.load_user_data(
        neo4j_session,
        user_data,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "PXPGF42",
        "PAM4FGS",
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:PagerDutyUser) RETURN n.id;
        """,
    )
    actual_nodes = {n["n.id"] for n in nodes}
    assert actual_nodes == expected_nodes
