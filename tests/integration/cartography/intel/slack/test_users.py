from unittest.mock import Mock

import pytest

import cartography.intel.slack.teams
import cartography.intel.slack.users
from tests.data.slack.users import SLACK_BOT_TURNED_USER
from tests.data.slack.users import SLACK_USER_TURNED_BOT
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


@pytest.mark.parametrize(
    "members_after, member_id, expected_labels, former_kind_property",
    [
        pytest.param(
            SLACK_USER_TURNED_BOT,
            "SLACKUSER2",
            {"SlackBot", "ThirdPartyApp", "SlackUser"},
            "email",
            id="user_to_bot",
        ),
        pytest.param(
            SLACK_BOT_TURNED_USER,
            "SLACKBOT1",
            {"SlackUser", "UserAccount"},
            "is_bot",
            id="bot_to_user",
        ),
    ],
)
def test_member_kind_change_relabels_the_existing_node(
    neo4j_session,
    members_after,
    member_id,
    expected_labels,
    former_kind_property,
):
    _sync_teams_and_users(neo4j_session)
    node_before = neo4j_session.run(
        """
        MATCH (n:SlackUser{id: $id})
        RETURN elementId(n) AS element_id, n.firstseen AS firstseen
        """,
        id=member_id,
    ).single(strict=True)

    cartography.intel.slack.users.sync(
        neo4j_session,
        Mock(users_list=Mock(return_value=members_after)),
        SLACK_TEAM_ID,
        TEST_UPDATE_TAG + 1,
        {**COMMON_JOB_PARAMETERS, "UPDATE_TAG": TEST_UPDATE_TAG + 1},
    )

    node_after = neo4j_session.run(
        """
        MATCH (n{id: $id})
        RETURN elementId(n) AS element_id,
               n.firstseen AS firstseen,
               labels(n) AS labels,
               n[$former_kind_property] AS former_kind_value
        """,
        id=member_id,
        former_kind_property=former_kind_property,
    ).single(strict=True)
    assert node_after["element_id"] == node_before["element_id"]
    assert node_after["firstseen"] == node_before["firstseen"]
    assert set(node_after["labels"]) == expected_labels
    assert node_after["former_kind_value"] is None


def test_bot_that_an_older_version_refreshed_as_a_user_loses_the_user_label(
    neo4j_session,
):
    _sync_teams_and_users(neo4j_session)
    neo4j_session.run("MATCH (n:SlackBot{id: 'SLACKBOT1'}) SET n:UserAccount")

    _sync_teams_and_users(neo4j_session)

    labels = neo4j_session.run(
        "MATCH (n{id: 'SLACKBOT1'}) RETURN labels(n) AS labels",
    ).single(strict=True)["labels"]
    assert set(labels) == {"SlackBot", "ThirdPartyApp", "SlackUser"}
