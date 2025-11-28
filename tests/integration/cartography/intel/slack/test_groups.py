import cartography.intel.slack.channels
import cartography.intel.slack.groups
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


def test_load_slack_groups(neo4j_session):
    """
    Ensure that groups actually get loaded
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
    cartography.intel.slack.channels.sync(
        neo4j_session,
        slack_client,
        SLACK_TEAM_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )
    cartography.intel.slack.groups.sync(
        neo4j_session,
        slack_client,
        SLACK_TEAM_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMETERS,
    )

    # Assert groups exists
    expected_nodes = {
        ("SLACKGROUP1", "Mobile Dev team"),
        ("SLACKGROUP2", "Security Team"),
        ("SLACKGROUP3", "Empty Group"),
    }
    assert check_nodes(neo4j_session, "SlackGroup", ["id", "name"]) == expected_nodes

    # Assert groups are connected to team
    expected_rels = {
        ("SLACKGROUP1", SLACK_TEAM_ID),
        ("SLACKGROUP2", SLACK_TEAM_ID),
        ("SLACKGROUP3", SLACK_TEAM_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "SlackGroup",
            "id",
            "SlackTeam",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert groups are connected to Creator
    expected_rels = {
        ("SLACKGROUP1", "SLACKUSER1"),
        ("SLACKGROUP2", "SLACKUSER1"),
        ("SLACKGROUP3", "SLACKUSER1"),
    }
    assert (
        check_rels(
            neo4j_session,
            "SlackGroup",
            "id",
            "SlackUser",
            "id",
            "CREATED",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert groups are connected to Members
    expected_rels = {
        ("SLACKGROUP1", "SLACKUSER1"),
        ("SLACKGROUP2", "SLACKUSER1"),
        ("SLACKGROUP1", "SLACKUSER2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "SlackGroup",
            "id",
            "SlackUser",
            "id",
            "MEMBER_OF",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert groups are connected to channels
    expected_rels = {
        ("SLACKGROUP1", "SLACKCHANNEL1"),
        ("SLACKGROUP2", "SLACKCHANNEL2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "SlackGroup",
            "id",
            "SlackChannel",
            "id",
            "MEMBER_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )
