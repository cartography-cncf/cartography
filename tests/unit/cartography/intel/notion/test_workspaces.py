from unittest.mock import MagicMock

import pytest

from cartography.intel.notion.workspaces import get
from cartography.intel.notion.workspaces import transform
from tests.data.notion.users import TOKEN_USER


def test_get_current_bot_validates_response_shape():
    # Arrange
    api_session = MagicMock()
    api_session.get.return_value.json.return_value = []

    # Act and assert
    with pytest.raises(ValueError, match="JSON object"):
        get(api_session)


def test_transform_discovers_workspace_from_token_bot():
    # Act
    result = transform(TOKEN_USER)

    # Assert
    assert result == {
        "id": "workspace-1",
        "name": "Example Workspace",
        "token_bot_notion_user_id": "bot-1",
    }


def test_transform_rejects_personal_access_token_user():
    # Arrange
    token_user = {"object": "user", "id": "person-1", "type": "person"}

    # Act and assert
    with pytest.raises(ValueError, match="personal access tokens"):
        transform(token_user)


@pytest.mark.parametrize(
    "token_user",
    [
        {"object": "user", "id": "bot-1", "type": "bot", "bot": []},
        {"object": "user", "id": "bot-1", "type": "bot", "bot": {}},
        {
            "object": "user",
            "id": "bot-1",
            "type": "bot",
            "bot": {"workspace_id": "workspace-1", "workspace_name": []},
        },
    ],
)
def test_transform_rejects_malformed_workspace_details(token_user):
    # Act and assert
    with pytest.raises(ValueError):
        transform(token_user)
