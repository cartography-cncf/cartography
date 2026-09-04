from unittest.mock import MagicMock

import pytest

import cartography.intel.notion.pages
import cartography.intel.notion.users
import cartography.intel.notion.workspaces
from tests.data.notion.pages import PUBLIC_PAGE
from tests.data.notion.users import TOKEN_USER
from tests.data.notion.users import USERS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_WORKSPACE_ID = "workspace-1"


def _response(payload, status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload
    return response


def _seed_workspace_and_users(neo4j_session):
    workspace = cartography.intel.notion.workspaces.transform(TOKEN_USER)
    workspace["token_user"] = TOKEN_USER
    cartography.intel.notion.workspaces.sync(
        neo4j_session,
        workspace,
        TEST_UPDATE_TAG,
    )
    api_session = MagicMock()
    api_session.get.return_value = _response(
        {"results": USERS, "has_more": False, "next_cursor": None},
    )
    cartography.intel.notion.users.sync(
        neo4j_session,
        api_session,
        workspace,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "WORKSPACE_ID": TEST_WORKSPACE_ID},
    )


def test_sync_public_pages_and_creator_relationship(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _seed_workspace_and_users(neo4j_session)
    api_session = MagicMock()
    api_session.post.return_value = _response(
        {"results": [PUBLIC_PAGE], "has_more": False, "next_cursor": None},
    )

    # Act
    cartography.intel.notion.pages.sync(
        neo4j_session,
        api_session,
        TEST_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "NotionPage",
        ["id", "title", "public_url", "parent_notion_id", "is_public"],
    ) == {
        (
            "workspace-1/page-public",
            "Public security guidance",
            "https://example.notion.site/page-public",
            "page-parent",
            True,
        ),
    }
    assert check_rels(
        neo4j_session,
        "NotionWorkspace",
        "id",
        "NotionPage",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {("workspace-1", "workspace-1/page-public")}
    assert check_rels(
        neo4j_session,
        "NotionPage",
        "id",
        "NotionUser",
        "id",
        "CREATED_BY",
        rel_direction_right=True,
    ) == {("workspace-1/page-public", "workspace-1/person-1")}


def test_sync_deletes_only_confirmed_unpublished_pages(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _seed_workspace_and_users(neo4j_session)
    first_session = MagicMock()
    first_session.post.return_value = _response(
        {"results": [PUBLIC_PAGE], "has_more": False, "next_cursor": None},
    )
    cartography.intel.notion.pages.sync(
        neo4j_session,
        first_session,
        TEST_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )
    unpublished_page = {**PUBLIC_PAGE, "public_url": None}
    second_session = MagicMock()
    second_session.post.return_value = _response(
        {"results": [unpublished_page], "has_more": False, "next_cursor": None},
    )

    # Act
    cartography.intel.notion.pages.sync(
        neo4j_session,
        second_session,
        TEST_WORKSPACE_ID,
        TEST_UPDATE_TAG + 1,
    )

    # Assert
    assert check_nodes(neo4j_session, "NotionPage", ["id"]) == set()


def test_sync_preserves_page_omitted_from_non_authoritative_search(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _seed_workspace_and_users(neo4j_session)
    first_session = MagicMock()
    first_session.post.return_value = _response(
        {"results": [PUBLIC_PAGE], "has_more": False, "next_cursor": None},
    )
    cartography.intel.notion.pages.sync(
        neo4j_session,
        first_session,
        TEST_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )
    second_session = MagicMock()
    second_session.post.return_value = _response(
        {"results": [], "has_more": False, "next_cursor": None},
    )

    # Act
    cartography.intel.notion.pages.sync(
        neo4j_session,
        second_session,
        TEST_WORKSPACE_ID,
        TEST_UPDATE_TAG + 1,
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "NotionPage",
        ["id", "lastupdated"],
    ) == {("workspace-1/page-public", TEST_UPDATE_TAG)}
    second_session.get.assert_not_called()


def test_sync_preserves_page_when_search_pagination_fails(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _seed_workspace_and_users(neo4j_session)
    first_session = MagicMock()
    first_session.post.return_value = _response(
        {"results": [PUBLIC_PAGE], "has_more": False, "next_cursor": None},
    )
    cartography.intel.notion.pages.sync(
        neo4j_session,
        first_session,
        TEST_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )
    failed_session = MagicMock()
    failed_session.post.return_value = _response(
        {"results": [], "has_more": True, "next_cursor": None},
    )

    # Act and assert
    with pytest.raises(ValueError):
        cartography.intel.notion.pages.sync(
            neo4j_session,
            failed_session,
            TEST_WORKSPACE_ID,
            TEST_UPDATE_TAG + 1,
        )
    assert check_nodes(
        neo4j_session,
        "NotionPage",
        ["id", "lastupdated"],
    ) == {("workspace-1/page-public", TEST_UPDATE_TAG)}
