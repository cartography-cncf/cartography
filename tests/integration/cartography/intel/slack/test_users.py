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


def _sync_teams_and_users(neo4j_session):
    """Helper to sync teams and users for tests."""
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


def test_load_slack_users(neo4j_session):
    """
    Ensure that human users get loaded as SlackUser with UserAccount label.
    Bots also carry the deprecated SlackUser extra label for backward compat,
    so MATCH (n:SlackUser) returns all members.
    """
    _sync_teams_and_users(neo4j_session)

    # All members are queryable via SlackUser label (backward compat)
    expected_all = {
        ("SLACKUSER1", "mbsimpson@simpson.corp"),
        ("SLACKUSER2", "hjsimpson@simpson.corp"),
        ("SLACKBOT1", None),
    }
    assert check_nodes(neo4j_session, "SlackUser", ["id", "email"]) == expected_all

    # Only human users have UserAccount label
    expected_user_accounts = {
        ("SLACKUSER1",),
        ("SLACKUSER2",),
    }
    assert check_nodes(neo4j_session, "UserAccount", ["id"]) == expected_user_accounts

    # All members are connected to Team via SlackUser label
    expected_rels = {
        ("SLACKUSER1", SLACK_TEAM_ID),
        ("SLACKUSER2", SLACK_TEAM_ID),
        ("SLACKBOT1", SLACK_TEAM_ID),
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


def test_load_slack_bots(neo4j_session):
    """
    Ensure that bots get loaded as SlackBot with ThirdPartyApp and
    deprecated SlackUser labels.
    """
    _sync_teams_and_users(neo4j_session)

    # Bots have SlackBot as primary label
    expected_bots = {
        ("SLACKBOT1", "securitybot"),
    }
    assert check_nodes(neo4j_session, "SlackBot", ["id", "name"]) == expected_bots

    # Bots have ThirdPartyApp label
    expected_apps = {
        ("SLACKBOT1",),
    }
    assert check_nodes(neo4j_session, "ThirdPartyApp", ["id"]) == expected_apps

    # Bots are connected to Team
    expected_rels = {
        ("SLACKBOT1", SLACK_TEAM_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "SlackBot",
            "id",
            "SlackTeam",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Bots do NOT have UserAccount label
    assert check_nodes(neo4j_session, "UserAccount", ["id"]) & {("SLACKBOT1",)} == set()
