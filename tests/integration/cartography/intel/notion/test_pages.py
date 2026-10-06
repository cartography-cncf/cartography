from unittest.mock import MagicMock

import pytest
import requests

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


def _search_payload(results, has_more=False, next_cursor=None):
    return {
        "object": "list",
        "type": "page_or_data_source",
        "page_or_data_source": {},
        "results": results,
        "has_more": has_more,
        "next_cursor": next_cursor,
    }


def _seed_workspace_and_users(neo4j_session):
    workspace = cartography.intel.notion.workspaces.transform(TOKEN_USER)
    workspace["token_user"] = TOKEN_USER
    cartography.intel.notion.workspaces.load_workspace(
        neo4j_session,
        workspace,
        TEST_UPDATE_TAG,
    )
    api_session = MagicMock()
    api_session.get.return_value = _response(
        {
            "object": "list",
            "type": "user",
            "user": {},
            "results": USERS,
            "has_more": False,
            "next_cursor": None,
        },
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
    bot_page = {
        **PUBLIC_PAGE,
        "id": "page-created-by-bot",
        "created_by": {"object": "user", "id": "bot-1"},
        "url": "https://www.notion.so/page-created-by-bot",
        "public_url": "https://example.notion.site/page-created-by-bot",
    }
    api_session = MagicMock()
    api_session.post.side_effect = [
        _response(_search_payload([PUBLIC_PAGE], True, "next-page")),
        _response(_search_payload([bot_page])),
    ]

    # Act
    cartography.intel.notion.pages.sync(
        neo4j_session,
        api_session,
        TEST_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    assert api_session.post.call_args_list[1].kwargs["json"]["start_cursor"] == (
        "next-page"
    )
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
        (
            "workspace-1/page-created-by-bot",
            "Public security guidance",
            "https://example.notion.site/page-created-by-bot",
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
    ) == {
        ("workspace-1", "workspace-1/page-created-by-bot"),
        ("workspace-1", "workspace-1/page-public"),
    }
    assert check_rels(
        neo4j_session,
        "NotionPage",
        "id",
        "NotionUser",
        "id",
        "CREATED_BY",
        rel_direction_right=True,
    ) == {("workspace-1/page-public", "workspace-1/person-1")}
    assert check_rels(
        neo4j_session,
        "NotionPage",
        "id",
        "NotionBot",
        "id",
        "CREATED_BY",
        rel_direction_right=True,
    ) == {("workspace-1/page-created-by-bot", "workspace-1/bot-1")}


def test_sync_deletes_only_confirmed_unpublished_pages(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _seed_workspace_and_users(neo4j_session)
    first_session = MagicMock()
    first_session.post.return_value = _response(
        _search_payload([PUBLIC_PAGE]),
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
        _search_payload([unpublished_page]),
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


def test_sync_preserves_page_seen_public_after_unpublished(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _seed_workspace_and_users(neo4j_session)
    unpublished_page = {**PUBLIC_PAGE, "public_url": None}
    api_session = MagicMock()
    api_session.post.side_effect = [
        _response(_search_payload([unpublished_page], True, "next-page")),
        _response(_search_payload([PUBLIC_PAGE])),
    ]

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
        ["id", "public_url"],
    ) == {
        (
            "workspace-1/page-public",
            "https://example.notion.site/page-public",
        ),
    }


def _sync_public_page_then_omit_it(neo4j_session, page_lookup_response):
    _seed_workspace_and_users(neo4j_session)
    first_session = MagicMock()
    first_session.post.return_value = _response(
        _search_payload([PUBLIC_PAGE]),
    )
    cartography.intel.notion.pages.sync(
        neo4j_session,
        first_session,
        TEST_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )
    second_session = MagicMock()
    second_session.post.return_value = _response(
        _search_payload([]),
    )
    second_session.get.return_value = page_lookup_response
    cartography.intel.notion.pages.sync(
        neo4j_session,
        second_session,
        TEST_WORKSPACE_ID,
        TEST_UPDATE_TAG + 1,
    )
    return second_session


def test_sync_refreshes_page_omitted_from_search_but_still_public(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Act
    second_session = _sync_public_page_then_omit_it(
        neo4j_session,
        _response(PUBLIC_PAGE),
    )

    # Assert
    second_session.get.assert_called_once()
    assert second_session.get.call_args.args[0].endswith("/pages/page-public")
    assert check_nodes(
        neo4j_session,
        "NotionPage",
        ["id", "lastupdated"],
    ) == {("workspace-1/page-public", TEST_UPDATE_TAG + 1)}
    assert check_rels(
        neo4j_session,
        "NotionPage",
        "id",
        "NotionUser",
        "id",
        "CREATED_BY",
        rel_direction_right=True,
    ) == {("workspace-1/page-public", "workspace-1/person-1")}


def test_sync_expires_page_omitted_from_search_and_not_found(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Act
    _sync_public_page_then_omit_it(
        neo4j_session,
        _response({"object": "error", "code": "object_not_found"}, 404),
    )

    # Assert
    assert check_nodes(neo4j_session, "NotionPage", ["id"]) == set()


def test_sync_expires_page_omitted_from_search_and_unpublished(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Act
    _sync_public_page_then_omit_it(
        neo4j_session,
        _response({**PUBLIC_PAGE, "public_url": None}),
    )

    # Assert
    assert check_nodes(neo4j_session, "NotionPage", ["id"]) == set()


def test_sync_preserves_page_when_lookup_fails(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    failed_lookup = _response({}, 500)
    failed_lookup.raise_for_status.side_effect = requests.HTTPError("server error")

    # Act and assert
    with pytest.raises(requests.HTTPError):
        _sync_public_page_then_omit_it(neo4j_session, failed_lookup)
    assert check_nodes(
        neo4j_session,
        "NotionPage",
        ["id", "lastupdated"],
    ) == {("workspace-1/page-public", TEST_UPDATE_TAG)}


def test_sync_preserves_page_when_search_pagination_fails(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _seed_workspace_and_users(neo4j_session)
    first_session = MagicMock()
    first_session.post.return_value = _response(
        _search_payload([PUBLIC_PAGE]),
    )
    cartography.intel.notion.pages.sync(
        neo4j_session,
        first_session,
        TEST_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )
    failed_session = MagicMock()
    unpublished_page = {**PUBLIC_PAGE, "public_url": None}
    new_public_page = {
        **PUBLIC_PAGE,
        "id": "page-new",
        "url": "https://www.notion.so/page-new",
        "public_url": "https://example.notion.site/page-new",
    }
    failed_session.post.side_effect = [
        _response(_search_payload([unpublished_page, new_public_page], True, "c2")),
        _response({"results": [], "has_more": False}),
    ]

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


def test_sync_preserves_page_when_search_is_incomplete(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _seed_workspace_and_users(neo4j_session)
    first_session = MagicMock()
    first_session.post.return_value = _response(_search_payload([PUBLIC_PAGE]))
    cartography.intel.notion.pages.sync(
        neo4j_session,
        first_session,
        TEST_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )
    incomplete_payload = _search_payload([{**PUBLIC_PAGE, "public_url": None}])
    incomplete_payload["request_status"] = {
        "type": "incomplete",
        "incomplete_reason": "query_result_limit_reached",
    }
    incomplete_session = MagicMock()
    incomplete_session.post.return_value = _response(incomplete_payload)

    # Act and assert
    with pytest.raises(ValueError, match="incomplete result set"):
        cartography.intel.notion.pages.sync(
            neo4j_session,
            incomplete_session,
            TEST_WORKSPACE_ID,
            TEST_UPDATE_TAG + 1,
        )

    assert check_nodes(
        neo4j_session,
        "NotionPage",
        ["id", "lastupdated"],
    ) == {("workspace-1/page-public", TEST_UPDATE_TAG)}


def test_cleanup_is_scoped_to_workspace(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _seed_workspace_and_users(neo4j_session)
    workspace_two_token = {
        **TOKEN_USER,
        "bot": {
            **TOKEN_USER["bot"],
            "workspace_id": "workspace-2",
            "workspace_name": "Workspace Two",
        },
    }
    workspace_two = cartography.intel.notion.workspaces.transform(workspace_two_token)
    cartography.intel.notion.workspaces.load_workspace(
        neo4j_session,
        workspace_two,
        TEST_UPDATE_TAG,
    )
    for workspace_id in (TEST_WORKSPACE_ID, "workspace-2"):
        api_session = MagicMock()
        api_session.post.return_value = _response(_search_payload([PUBLIC_PAGE]))
        cartography.intel.notion.pages.sync(
            neo4j_session,
            api_session,
            workspace_id,
            TEST_UPDATE_TAG,
        )

    # Act
    cartography.intel.notion.pages.cleanup(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "WORKSPACE_ID": TEST_WORKSPACE_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, "NotionPage", ["id"]) == {
        ("workspace-2/page-public",),
    }
    assert check_rels(
        neo4j_session,
        "NotionWorkspace",
        "id",
        "NotionPage",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {("workspace-2", "workspace-2/page-public")}
