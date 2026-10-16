import asyncio
from datetime import datetime
from datetime import timezone
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from kiota_abstractions.api_error import APIError
from msgraph.generated.models.directory_object import DirectoryObject
from msgraph.generated.models.sign_in_activity import SignInActivity
from msgraph.generated.models.user import User
from msgraph.generated.models.user_collection_response import UserCollectionResponse
from msgraph.generated.users.users_request_builder import UsersRequestBuilder

from cartography.intel.microsoft.entra.users import get_users
from cartography.intel.microsoft.entra.users import transform_users
from cartography.intel.microsoft.entra.users import USER_SELECT_FIELDS


def test_activity_timestamps_and_missing_activity() -> None:
    # Arrange
    successful = datetime(2024, 1, 1, tzinfo=timezone.utc)
    interactive = datetime(2024, 2, 1, tzinfo=timezone.utc)
    non_interactive = datetime(2024, 3, 1, tzinfo=timezone.utc)
    users = [
        User(
            id="active-user",
            manager=DirectoryObject(id="manager"),
            sign_in_activity=SignInActivity(
                last_successful_sign_in_date_time=successful,
                last_sign_in_date_time=interactive,
                last_non_interactive_sign_in_date_time=non_interactive,
            ),
        ),
        User(id="unknown-user"),
        User(id="empty-activity", sign_in_activity=SignInActivity()),
    ]

    # Act
    result = list(transform_users(users, activity_available=True))

    # Assert
    assert result[0]["last_successful_sign_in_date_time"] == successful
    assert result[0]["last_sign_in_date_time"] == interactive
    assert result[0]["last_non_interactive_sign_in_date_time"] == non_interactive
    assert result[0]["manager_id"] == "manager"
    assert result[0]["sign_in_activity_available"] is True
    assert result[1]["sign_in_activity_available"] is True
    assert result[2]["sign_in_activity_available"] is True
    for row in result[1:]:
        assert row["last_successful_sign_in_date_time"] is None
        assert row["last_sign_in_date_time"] is None
        assert row["last_non_interactive_sign_in_date_time"] is None


@pytest.mark.parametrize("risk_readable", [True, False])  # type: ignore[misc]
@pytest.mark.parametrize("registrations_readable", [True, False])  # type: ignore[misc]
def test_transform_merges_mfa_registration_and_risk(
    registrations_readable: bool, risk_readable: bool
) -> None:
    # Arrange
    registrations = {
        "listed": {
            "is_mfa_registered": True,
            "is_mfa_capable": True,
            "mfa_methods_registered": ["fido2"],
        },
    }
    risky_users = {
        "listed": {
            "risk_level": "high",
            "risk_state": "atRisk",
            "risk_detail": "none",
            "risk_last_updated_date_time": None,
        },
    }
    users = [User(id="listed"), User(id="unlisted")]

    # Act
    listed, unlisted = transform_users(
        users,
        activity_available=True,
        mfa_registrations=registrations if registrations_readable else None,
        risky_users=risky_users if risk_readable else None,
    )

    # Assert: each report's flag and fields follow only that report.
    for row in (listed, unlisted):
        assert row["mfa_registration_available"] is registrations_readable
        assert row["risk_available"] is risk_readable
    assert listed["is_mfa_registered"] is (True if registrations_readable else None)
    assert listed["risk_level"] == ("high" if risk_readable else None)
    for field in ("is_mfa_registered", "mfa_methods_registered", "risk_level"):
        assert unlisted[field] is None


def _client() -> MagicMock:
    client = MagicMock()
    client.users.UsersRequestBuilderGetRequestConfiguration = (
        UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration
    )
    client.users.UsersRequestBuilderGetQueryParameters = (
        UsersRequestBuilder.UsersRequestBuilderGetQueryParameters
    )
    return client


async def _collect(client: MagicMock) -> list[tuple[list[User], bool]]:
    return [page async for page in get_users(client)]


def test_activity_request_paginates() -> None:
    # Arrange
    client = _client()
    first, second = User(id="first"), User(id="second")
    next_link = "https://graph.microsoft.com/v1.0/users?$skiptoken=synthetic"
    client.users.get = AsyncMock(
        return_value=UserCollectionResponse(value=[first], odata_next_link=next_link)
    )
    client.users.with_url.return_value.get = AsyncMock(
        return_value=UserCollectionResponse(value=[second])
    )

    # Act
    result = asyncio.run(_collect(client))

    # Assert
    assert result == [([first], True), ([second], True)]
    parameters = client.users.get.call_args.kwargs[
        "request_configuration"
    ].query_parameters
    assert parameters.top == 500
    assert "signInActivity" in parameters.select
    assert set(USER_SELECT_FIELDS) <= set(parameters.select)
    assert "manager($select=id)" in parameters.expand
    client.users.with_url.assert_called_once_with(next_link)


@pytest.mark.parametrize("status", [400, 401, 429, 500])  # type: ignore[misc]
def test_non_forbidden_errors_propagate(status: int) -> None:
    # Arrange
    client = _client()
    client.users.get = AsyncMock(
        side_effect=APIError("request failed", response_status_code=status)
    )

    # Act and assert
    with pytest.raises(APIError):
        asyncio.run(_collect(client))
    client.users.get.assert_awaited_once()


def test_failed_fallback_propagates() -> None:
    # Arrange
    client = _client()
    client.users.get = AsyncMock(
        side_effect=APIError("forbidden", response_status_code=403)
    )

    # Act and assert
    with pytest.raises(APIError):
        asyncio.run(_collect(client))
    assert client.users.get.await_count == 2
