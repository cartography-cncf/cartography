from typing import Any
from unittest.mock import patch

import requests

import cartography.intel.opsgenie.resources
import tests.data.opsgenie.data
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://api.opsgenie.com"


def _sync(
    neo4j_session,
    update_tag: int,
    teams: list[dict[str, Any]],
    team_members: dict[str, list[dict[str, Any]]],
    users: list[dict[str, Any]],
    schedules: list[dict[str, Any]],
) -> None:
    resources = cartography.intel.opsgenie.resources
    with (
        patch.object(
            resources,
            "get_account",
            return_value=tests.data.opsgenie.data.ACCOUNT,
        ),
        patch.object(resources, "get_teams", return_value=teams),
        patch.object(
            resources,
            "get_team_members",
            side_effect=lambda _session, _base_url, _timeout, team_id: team_members[
                team_id
            ],
        ),
        patch.object(resources, "get_users", return_value=users),
        patch.object(resources, "get_schedules", return_value=schedules),
    ):
        resources.sync(
            neo4j_session,
            requests.Session(),
            TEST_BASE_URL,
            60,
            update_tag,
            {"UPDATE_TAG": update_tag},
        )


def test_sync_opsgenie(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Act
    _sync(
        neo4j_session,
        TEST_UPDATE_TAG,
        tests.data.opsgenie.data.TEAMS,
        tests.data.opsgenie.data.TEAM_MEMBERS,
        tests.data.opsgenie.data.USERS,
        tests.data.opsgenie.data.SCHEDULES,
    )

    # Assert
    assert check_nodes(neo4j_session, "OpsgenieAccount", ["id", "name"]) == {
        ("example-account", "example-account"),
    }
    assert check_nodes(neo4j_session, "OpsgenieTeam", ["id", "name"]) == {
        ("team-1", "Platform"),
        ("team-2", "Payments"),
    }
    assert check_nodes(neo4j_session, "OpsgenieUser", ["id", "username"]) == {
        ("user-1", "alice@example.com"),
        ("user-2", "bob@example.com"),
    }
    assert check_nodes(neo4j_session, "OpsgenieSchedule", ["id", "name"]) == {
        ("schedule-1", "Platform Primary"),
        ("schedule-2", "Payments Primary"),
    }
    assert check_nodes(neo4j_session, "Tenant", ["id"]) == {("example-account",)}
    assert check_nodes(neo4j_session, "UserGroup", ["id"]) == {
        ("team-1",),
        ("team-2",),
    }
    assert check_nodes(neo4j_session, "UserAccount", ["id"]) == {
        ("user-1",),
        ("user-2",),
    }
    assert check_rels(
        neo4j_session,
        "OpsgenieAccount",
        "id",
        "OpsgenieTeam",
        "id",
        "RESOURCE",
    ) == {("example-account", "team-1"), ("example-account", "team-2")}
    assert check_rels(
        neo4j_session,
        "OpsgenieAccount",
        "id",
        "OpsgenieUser",
        "id",
        "RESOURCE",
    ) == {("example-account", "user-1"), ("example-account", "user-2")}
    assert check_rels(
        neo4j_session,
        "OpsgenieAccount",
        "id",
        "OpsgenieSchedule",
        "id",
        "RESOURCE",
    ) == {
        ("example-account", "schedule-1"),
        ("example-account", "schedule-2"),
    }
    assert check_rels(
        neo4j_session,
        "OpsgenieSchedule",
        "id",
        "OpsgenieTeam",
        "id",
        "OWNED_BY",
    ) == {("schedule-1", "team-1"), ("schedule-2", "team-2")}
    assert check_rels(
        neo4j_session,
        "OpsgenieUser",
        "id",
        "OpsgenieTeam",
        "id",
        "MEMBER_OF",
    ) == {("user-1", "team-1"), ("user-2", "team-1"), ("user-2", "team-2")}


def test_sync_opsgenie_removes_stale_data(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    data = tests.data.opsgenie.data
    _sync(
        neo4j_session,
        TEST_UPDATE_TAG,
        data.TEAMS,
        data.TEAM_MEMBERS,
        data.USERS,
        data.SCHEDULES,
    )

    # Act: user-2 leaves team-1 but both still exist, and schedule-2 is deleted.
    _sync(
        neo4j_session,
        TEST_UPDATE_TAG + 1,
        data.TEAMS,
        {
            "team-1": data.TEAM_MEMBERS["team-1"][:1],
            "team-2": data.TEAM_MEMBERS["team-2"],
        },
        data.USERS,
        data.SCHEDULES[:1],
    )

    # Assert
    assert check_nodes(neo4j_session, "OpsgenieTeam", ["id"]) == {
        ("team-1",),
        ("team-2",),
    }
    assert check_nodes(neo4j_session, "OpsgenieUser", ["id"]) == {
        ("user-1",),
        ("user-2",),
    }
    assert check_nodes(neo4j_session, "OpsgenieSchedule", ["id"]) == {
        ("schedule-1",),
    }
    assert check_rels(
        neo4j_session,
        "OpsgenieUser",
        "id",
        "OpsgenieTeam",
        "id",
        "MEMBER_OF",
    ) == {("user-1", "team-1"), ("user-2", "team-2")}
