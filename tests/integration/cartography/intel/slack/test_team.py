import cartography.intel.slack.teams
from tests.integration.cartography.intel.slack.utils import slack_client
from tests.integration.util import check_nodes

SLACK_TEAM_ID = "TTPQ4FBPT"
SLACK_TOKEN = "fake-token"
TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMETERS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "CHANNELS_MEMBERSHIPS": True,
}


def test_load_slack_team(neo4j_session):
    """
    Ensure that teams actually get loaded
    """  # Act
    cartography.intel.slack.teams.sync(
        neo4j_session,
        slack_client,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )

    # Assert Team exists
    expected_nodes = {
        (SLACK_TEAM_ID, "Simpson Corp"),
    }
    assert check_nodes(neo4j_session, "SlackTeam", ["id", "name"]) == expected_nodes
