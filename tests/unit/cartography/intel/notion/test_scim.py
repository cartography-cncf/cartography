import pytest

from cartography.intel.notion.scim import transform_groups
from cartography.intel.notion.scim import transform_users
from tests.data.notion.scim import SCIM_GROUPS
from tests.data.notion.scim import SCIM_USERS

PUBLIC_PEOPLE = [
    {
        "id": "workspace-1/person-1",
        "notion_user_id": "person-1",
        "name": "Public Alice",
        "email": "alice@example.com",
    },
    {
        "id": "workspace-1/person-2",
        "notion_user_id": "person-2",
        "name": "Public Bob",
        "email": "bob@example.com",
    },
]


def test_transform_users_merges_fields_and_resolves_manager():
    # Act
    users, managers = transform_users(SCIM_USERS, PUBLIC_PEOPLE, "workspace-1")

    # Assert
    alice = next(user for user in users if user["notion_user_id"] == "person-1")
    bob = next(user for user in users if user["notion_user_id"] == "person-2")
    assert alice == {
        "id": "workspace-1/person-1",
        "notion_user_id": "person-1",
        "name": "Alice Example",
        "email": "alice@example.com",
        "active": True,
        "workspace_role": "owner",
        "scim_external_id": "employee-alice",
        "title": "Security Engineer",
        "user_type": "Employee",
        "locale": "en-US",
        "preferred_language": "en",
        "department": "Security",
        "division": "Engineering",
        "cost_center": "CC-42",
        "organization": "Example Corp",
        "employee_number": "E-1",
        "manager_email": None,
        "is_workspace_member": True,
    }
    assert bob["name"] == "Bob Example"
    assert bob["manager_email"] == "alice@example.com"
    assert managers == [
        {
            "source_id": "workspace-1/person-2",
            "target_id": "workspace-1/person-1",
        },
    ]


def test_transform_users_leaves_public_only_people_unconfirmed_and_clears_scim_fields():
    # Act
    users, managers = transform_users(SCIM_USERS[:1], PUBLIC_PEOPLE, "workspace-1")

    # Assert
    bob = next(user for user in users if user["notion_user_id"] == "person-2")
    assert bob["name"] == "Public Bob"
    assert bob["email"] == "bob@example.com"
    assert bob["is_workspace_member"] is None
    assert bob["workspace_role"] is None
    assert managers == []


def test_transform_groups_scopes_memberships():
    # Act
    groups = transform_groups(SCIM_GROUPS, "workspace-1")

    # Assert
    assert groups == [
        {
            "id": "workspace-1/group-1",
            "notion_group_id": "group-1",
            "name": "Security",
            "scim_external_id": "security-team",
            "member_ids": ["workspace-1/person-1", "workspace-1/person-2"],
        },
    ]


@pytest.mark.parametrize(
    "users",
    [
        [{"id": "person-1", "userName": None}],
        SCIM_USERS + [SCIM_USERS[0]],
    ],
)
def test_transform_users_rejects_malformed_or_duplicate_resources(users):
    # Act and assert
    with pytest.raises(ValueError):
        transform_users(users, PUBLIC_PEOPLE, "workspace-1")


def test_transform_groups_rejects_malformed_members():
    # Act and assert
    with pytest.raises(ValueError):
        transform_groups(
            [{"id": "group-1", "displayName": "Group", "members": [1]}],
            "workspace-1",
        )
