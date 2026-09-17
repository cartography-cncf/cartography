from unittest.mock import MagicMock

import pytest

from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.users import get
from cartography.intel.zoom.users import transform


def test_get_paginates_every_status_without_detail_calls():
    # Arrange
    client = MagicMock(spec=ZoomClient)
    client.get_users_page.side_effect = [
        {"users": [{"id": "u1"}], "next_page_token": "page2", "total_records": 2},
        {"users": [{"id": "u2"}], "next_page_token": "", "total_records": 2},
        {"users": [{"id": "u3"}]},
        {"users": [{"email": "pending@example.com"}]},
    ]

    # Act
    users = get(client)

    # Assert
    assert [user["status"] for user in users] == [
        "active",
        "active",
        "inactive",
        "pending",
    ]
    assert [call.args[0] for call in client.get_users_page.call_args_list] == [
        {"status": "active", "page_size": 2000},
        {"status": "active", "page_size": 2000, "next_page_token": "page2"},
        {"status": "inactive", "page_size": 2000},
        {"status": "pending", "page_size": 2000},
    ]


@pytest.mark.parametrize(
    "pages",
    [
        [
            {"users": [], "next_page_token": "same"},
            {"users": [], "next_page_token": "same"},
        ],
        [{"users": [], "total_records": 1}],
        [{"users": None}],
    ],
)
def test_get_rejects_incomplete_pages(pages):
    # Arrange
    client = MagicMock(spec=ZoomClient)
    client.get_users_page.side_effect = pages

    # Act and assert
    with pytest.raises(ValueError):
        get(client)


@pytest.mark.parametrize(
    "plan_type, label",
    [
        (1, "Basic"),
        (2, "Licensed"),
        (4, "Unassigned without Meetings Basic"),
        (99, "None (legacy SSO)"),
        (999, None),
    ],
)
def test_pending_identity_and_plan_types(plan_type, label):
    # Arrange
    users = [{"email": " Pending@Example.com ", "status": "pending", "type": plan_type}]

    # Act
    first = transform(users, "account-a")[0]
    second = transform(users, "account-b")[0]

    # Assert
    assert first["id"] == "account-a:pending:pending@example.com"
    assert second["id"] == "account-b:pending:pending@example.com"
    assert first["zoom_id"] is None
    assert first["email"] == "pending@example.com"
    assert first["type"] == plan_type
    assert first["plan_type"] == label


@pytest.mark.parametrize(
    "user",
    [
        {"email": "user@example.com", "status": "active", "type": 1},
        {"id": "u1", "email": " ", "status": "active", "type": 1},
        {"id": "u1", "status": "active", "type": 1},
        {"id": "u1", "email": "user@example.com", "status": "active"},
    ],
)
def test_transform_rejects_missing_identity_and_license(user):
    # Arrange / Act and assert
    with pytest.raises((ValueError, KeyError)):
        transform([user], "account-a")
