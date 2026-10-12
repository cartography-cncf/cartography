from unittest.mock import patch

import requests

import cartography.intel.opsgenie.resources
import tests.data.opsgenie.data
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://api.opsgenie.com"


@patch.object(
    cartography.intel.opsgenie.resources,
    "get_account",
    return_value=tests.data.opsgenie.data.ACCOUNT,
)
@patch.object(
    cartography.intel.opsgenie.resources,
    "get_teams",
    return_value=tests.data.opsgenie.data.TEAMS,
)
@patch.object(
    cartography.intel.opsgenie.resources,
    "get_team_members",
    side_effect=lambda _session, _base_url, _timeout, team_id: (
        tests.data.opsgenie.data.TEAM_MEMBERS[team_id]
    ),
)
@patch.object(
    cartography.intel.opsgenie.resources,
    "get_users",
    return_value=tests.data.opsgenie.data.USERS,
)
@patch.object(
    cartography.intel.opsgenie.resources,
    "get_schedules",
    return_value=tests.data.opsgenie.data.SCHEDULES,
)
def test_sync_opsgenie(
    mock_schedules,
    mock_users,
    mock_team_members,
    mock_teams,
    mock_account,
    neo4j_session,
):
    # Arrange
    api_session = requests.Session()

    # Act
    cartography.intel.opsgenie.resources.sync(
        neo4j_session,
        api_session,
        TEST_BASE_URL,
        60,
        TEST_UPDATE_TAG,
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
        "OpsgenieSchedule",
        "id",
        "OpsgenieTeam",
        "id",
        "OWNED_BY",
    ) == {("schedule-1", "team-1"), ("schedule-2", "team-2")}
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
        "OpsgenieUser",
        "id",
        "OpsgenieTeam",
        "id",
        "MEMBER_OF",
    ) == {("user-1", "team-1"), ("user-2", "team-1"), ("user-2", "team-2")}
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
