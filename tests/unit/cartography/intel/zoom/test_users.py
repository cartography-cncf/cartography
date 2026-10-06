from datetime import datetime
from datetime import timezone
from typing import Any
from unittest.mock import MagicMock

import pytest

from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.users import get
from cartography.intel.zoom.users import transform


def test_get_paginates_every_status_without_detail_calls() -> None:
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


@pytest.mark.parametrize(  # type: ignore[misc]
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
def test_get_rejects_incomplete_pages(pages: list[dict[str, Any]]) -> None:
    # Arrange
    client = MagicMock(spec=ZoomClient)
    client.get_users_page.side_effect = pages

    # Act and assert
    with pytest.raises(ValueError):
        get(client)


def test_get_bounds_advancing_pagination(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setattr("cartography.intel.zoom.users.DEFAULT_MAX_PAGES", 2)
    client = MagicMock(spec=ZoomClient)
    client.get_users_page.side_effect = [
        {"users": [], "next_page_token": "page-2"},
        {"users": [], "next_page_token": "page-3"},
    ]

    # Act and assert
    with pytest.raises(ValueError, match="page limit"):
        get(client)
    assert client.get_users_page.call_count == 2


@pytest.mark.parametrize(  # type: ignore[misc]
    "plan_type, label",
    [
        (1, "Basic"),
        (2, "Licensed"),
        (4, "Unassigned without Meetings Basic"),
        (99, "None (legacy SSO)"),
        (999, None),
    ],
)
def test_pending_identity_and_plan_types(plan_type: int, label: str | None) -> None:
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


@pytest.mark.parametrize(  # type: ignore[misc]
    "user",
    [
        {"email": "user@example.com", "status": "active", "type": 1},
        {"id": "u1", "email": " ", "status": "active", "type": 1},
        {"id": "u1", "status": "active", "type": 1},
        {"id": "u1", "email": "user@example.com", "status": "active"},
    ],
)
def test_transform_rejects_missing_identity_and_license(user: dict[str, Any]) -> None:
    # Arrange / Act and assert
    with pytest.raises((ValueError, KeyError)):
        transform([user], "account-a")


@pytest.mark.parametrize(  # type: ignore[misc]
    "timestamps, expected, warning_count",
    [
        ({}, None, 0),
        ({"user_created_at": None, "last_login_time": None}, None, 0),
        ({"user_created_at": "", "last_login_time": ""}, None, 0),
        (
            {
                "user_created_at": "2026-01-01T00:00:00Z",
                "last_login_time": "2026-01-01T00:00:00Z",
            },
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            0,
        ),
        ({"user_created_at": "invalid", "last_login_time": 123}, None, 2),
    ],
)
def test_optional_timestamps_preserve_membership(
    timestamps: dict[str, Any],
    expected: datetime | None,
    warning_count: int,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Arrange
    user = {
        "id": "user-1",
        "email": "user@example.com",
        "status": "active",
        "type": 2,
        **timestamps,
    }

    # Act
    result = transform([user], "account-a")

    # Assert
    assert len(result) == 1
    assert result[0]["id"] == "account-a:user:user-1"
    assert result[0]["created_at"] == expected
    assert result[0]["last_login_time"] == expected
    assert len(caplog.records) == warning_count


def test_cross_page_duplicate_identity_collapses_after_email_normalization() -> None:
    # Arrange
    client = MagicMock(spec=ZoomClient)
    client.get_users_page.side_effect = [
        {
            "users": [{"id": "user-1", "email": "User@Example.com", "type": 2}],
            "next_page_token": "next",
        },
        {"users": [{"id": "user-1", "email": " user@example.com ", "type": 2}]},
        {"users": []},
        {"users": []},
    ]

    # Act
    result = transform(get(client), "account-a")

    # Assert
    assert [(row["id"], row["email"]) for row in result] == [
        ("account-a:user:user-1", "user@example.com")
    ]
