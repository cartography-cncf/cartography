import cartography.intel.slack.teams
import cartography.intel.slack.users
from tests.integration.cartography.intel.slack.utils import slack_client
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

SLACK_TEAM_ID = "TTPQ4FBPT"
SLACK_TOKEN = "fake-token"
TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMETERS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "TEAM_ID": SLACK_TEAM_ID,
    "CHANNELS_MEMBERSHIPS": True,
}


def test_load_slack_users(neo4j_session):
    """
    Ensure that users actually get loaded
    """
    # Act
    cartography.intel.slack.teams.sync(
        neo4j_session,
        slack_client,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )
    cartography.intel.slack.users.sync(
        neo4j_session,
        slack_client,
        SLACK_TEAM_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )

    # Assert Users exists
    expected_nodes = {
        ("SLACKUSER1", "mbsimpson@simpson.corp"),
        ("SLACKUSER2", "hjsimpson@simpson.corp"),
    }
    assert check_nodes(neo4j_session, "SlackUser", ["id", "email"]) == expected_nodes

    # Assert Users are connected with Team
    expected_rels = {
        ("SLACKUSER1", SLACK_TEAM_ID),
        ("SLACKUSER2", SLACK_TEAM_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "SlackUser",
            "id",
            "SlackTeam",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
