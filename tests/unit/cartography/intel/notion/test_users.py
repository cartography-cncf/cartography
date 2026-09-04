import pytest

from cartography.intel.notion.users import transform
from tests.data.notion.users import TOKEN_USER
from tests.data.notion.users import USERS


def test_transform_splits_people_and_bots():
    # Act
    people, bots = transform(USERS, "workspace-1", TOKEN_USER)

    # Assert
    assert people == [
        {
            "id": "workspace-1/person-1",
            "notion_user_id": "person-1",
            "name": "Alice Example",
            "email": "alice@example.com",
            "is_workspace_member": True,
        },
        {
            "id": "workspace-1/person-2",
            "notion_user_id": "person-2",
            "name": "Bob Example",
            "email": None,
            "is_workspace_member": True,
        },
    ]
    assert bots[0]["owner_id"] == "workspace-1/person-1"
    assert bots[0]["owner_notion_user_id"] == "person-1"
    assert bots[0]["is_token_bot"] is True
    assert bots[1]["owner_id"] is None
    assert bots[1]["is_token_bot"] is False


def test_transform_rejects_unknown_user_type():
    # Arrange
    users = [{"id": "unknown-1", "type": "alien"}]

    # Act and assert
    with pytest.raises(ValueError, match="Unsupported Notion user type"):
        transform(users, "workspace-1", TOKEN_USER)


def test_transform_requires_id_and_type():
    # Act and assert
    with pytest.raises(ValueError, match="valid id"):
        transform([{"type": "person"}], "workspace-1", TOKEN_USER)


@pytest.mark.parametrize(
    "user",
    [
        {"id": "person-1", "type": "person", "person": []},
        {"id": "bot-malformed", "type": "bot", "bot": []},
        {"id": "bot-malformed", "type": "bot", "bot": {"owner": []}},
    ],
)
def test_transform_rejects_malformed_user_details(user):
    # Act and assert
    with pytest.raises(ValueError):
        transform([user], "workspace-1", TOKEN_USER)
