from unittest.mock import MagicMock

import cartography.intel.notion.users
import cartography.intel.notion.workspaces
from tests.data.notion.users import USERS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _response(results):
    response = MagicMock()
    response.json.return_value = {
        "results": results,
        "has_more": False,
        "next_cursor": None,
    }
    return response


def _sync(neo4j_session, workspace_id, workspace_name, raw_users, update_tag):
    cartography.intel.notion.workspaces.sync(
        neo4j_session,
        workspace_id,
        workspace_name,
        update_tag,
    )
    api_session = MagicMock()
    api_session.get.return_value = _response(raw_users)
    cartography.intel.notion.users.sync(
        neo4j_session,
        api_session,
        workspace_id,
        update_tag,
        {"UPDATE_TAG": update_tag, "WORKSPACE_ID": workspace_id},
    )


def test_sync_users_and_bots(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Act
    _sync(neo4j_session, "workspace-1", "Engineering", USERS, TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(neo4j_session, "NotionWorkspace", ["id", "name"]) == {
        ("workspace-1", "Engineering"),
    }
    assert check_nodes(
        neo4j_session,
        "NotionUser",
        ["id", "notion_user_id", "name", "email"],
    ) == {
        ("workspace-1/person-1", "person-1", "Alice Example", "alice@example.com"),
        ("workspace-1/person-2", "person-2", "Bob Example", None),
    }
    assert check_nodes(
        neo4j_session,
        "NotionBot",
        ["id", "notion_user_id", "name", "owner_type"],
    ) == {
        ("workspace-1/bot-1", "bot-1", "Security Exporter", "user"),
        ("workspace-1/bot-2", "bot-2", "Workspace Bot", "workspace"),
    }
    assert check_rels(
        neo4j_session,
        "NotionWorkspace",
        "id",
        "NotionUser",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("workspace-1", "workspace-1/person-1"),
        ("workspace-1", "workspace-1/person-2"),
    }
    assert check_rels(
        neo4j_session,
        "NotionBot",
        "id",
        "NotionUser",
        "id",
        "OWNED_BY",
        rel_direction_right=True,
    ) == {("workspace-1/bot-1", "workspace-1/person-1")}
    ontology = neo4j_session.run(
        """
        MATCH (w:NotionWorkspace {id: 'workspace-1'})
        MATCH (u:NotionUser {id: 'workspace-1/person-1'})
        MATCH (b:NotionBot {id: 'workspace-1/bot-1'})
        RETURN w._ont_name AS workspace_name,
               u._ont_email AS user_email,
               u._ont_source AS user_source,
               b._ont_client_id AS bot_client_id
        """,
    ).single()
    assert ontology == {
        "workspace_name": "Engineering",
        "user_email": "alice@example.com",
        "user_source": "notion",
        "bot_client_id": "workspace-1/bot-1",
    }


def test_cleanup_is_scoped_to_workspace(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync(neo4j_session, "workspace-1", "One", USERS, TEST_UPDATE_TAG)
    _sync(neo4j_session, "workspace-2", "Two", USERS, TEST_UPDATE_TAG)

    # Act
    _sync(
        neo4j_session,
        "workspace-1",
        "One",
        USERS[:1],
        TEST_UPDATE_TAG + 1,
    )

    # Assert
    assert check_nodes(neo4j_session, "NotionUser", ["id"]) == {
        ("workspace-1/person-1",),
        ("workspace-2/person-1",),
        ("workspace-2/person-2",),
    }
    assert check_nodes(neo4j_session, "NotionBot", ["id"]) == {
        ("workspace-2/bot-1",),
        ("workspace-2/bot-2",),
    }
