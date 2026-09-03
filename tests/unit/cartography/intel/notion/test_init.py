import base64
import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.config import Config
from cartography.intel.notion import start_notion_ingestion
from tests.data.notion.users import TOKEN_USER


def _config(workspaces):
    encoded = base64.b64encode(
        json.dumps({"workspaces": workspaces}).encode(),
    ).decode()
    return Config(
        neo4j_uri="bolt://example.invalid:7687",
        notion_config=encoded,
        update_tag=123456789,
    )


@patch("cartography.intel.notion.pages.sync")
@patch("cartography.intel.notion.users.sync")
@patch("cartography.intel.notion.workspaces.sync")
@patch("cartography.intel.notion.workspaces.get")
@patch("cartography.intel.notion.create_api_session")
def test_start_discovers_workspace_and_honors_public_page_option(
    create_api_session,
    get_workspace,
    sync_workspace,
    sync_users,
    sync_pages,
):
    # Arrange
    api_session = MagicMock()
    create_api_session.return_value = api_session
    get_workspace.return_value = TOKEN_USER

    # Act
    start_notion_ingestion(
        MagicMock(),
        _config([{"api_token": "token", "sync_public_pages": True}]),
    )

    # Assert
    workspace = sync_workspace.call_args.args[1]
    assert workspace["id"] == "workspace-1"
    assert workspace["name"] == "Example Workspace"
    sync_users.assert_called_once()
    sync_pages.assert_called_once()
    api_session.close.assert_called_once()


@patch("cartography.intel.notion.users.sync")
@patch("cartography.intel.notion.workspaces.sync")
@patch("cartography.intel.notion.workspaces.get")
@patch("cartography.intel.notion.create_api_session")
def test_start_rejects_duplicate_discovered_workspaces_before_writes(
    create_api_session,
    get_workspace,
    sync_workspace,
    sync_users,
):
    # Arrange
    first_session = MagicMock()
    second_session = MagicMock()
    create_api_session.side_effect = [first_session, second_session]
    get_workspace.side_effect = [TOKEN_USER, TOKEN_USER]

    # Act and assert
    with pytest.raises(ValueError, match="same workspace"):
        start_notion_ingestion(
            MagicMock(),
            _config([{"api_token": "one"}, {"api_token": "two"}]),
        )
    sync_workspace.assert_not_called()
    sync_users.assert_not_called()
    first_session.close.assert_called_once()
    second_session.close.assert_called_once()
