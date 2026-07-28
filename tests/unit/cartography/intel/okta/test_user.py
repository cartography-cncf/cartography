from unittest import mock

import pytest

from cartography.intel.okta.users import _get_okta_users
from cartography.intel.okta.users import transform_okta_user
from tests.data.okta.users import create_test_user


@mock.patch("cartography.intel.okta.users.check_rate_limit", return_value=None)
def test_get_okta_users_includes_last_page(
    _mock_rate_limit: mock.MagicMock,
) -> None:
    """Okta user pagination should include the final page before stopping."""
    first_page = mock.MagicMock()
    first_page.result = ["first-user"]
    first_page.is_last_page.return_value = False
    first_page.next_url = "https://example.okta.com/api/v1/users?after=first"

    last_page = mock.MagicMock()
    last_page.result = ["last-user"]
    last_page.is_last_page.return_value = True
    last_page.next_url = None

    user_client = mock.MagicMock()
    user_client.get_paged_users.side_effect = [first_page, last_page]

    result = _get_okta_users(user_client)

    assert result == ["first-user", "last-user"]
    user_client.get_paged_users.assert_has_calls(
        [
            mock.call(),
            mock.call(url="https://example.okta.com/api/v1/users?after=first"),
        ],
    )


@mock.patch("cartography.intel.okta.users.check_rate_limit", return_value=None)
def test_get_okta_users_raises_on_malformed_next_link(
    _mock_rate_limit: mock.MagicMock,
) -> None:
    """
    A next link present but missing its URL must raise instead of silently
    re-fetching the first page forever.
    """
    paged_users = mock.MagicMock()
    paged_users.result = []
    paged_users.is_last_page.return_value = False
    paged_users.next_url = None
    user_client = mock.MagicMock()
    user_client.get_paged_users.return_value = paged_users

    with pytest.raises(ValueError, match="missing a next URL"):
        _get_okta_users(user_client)


def test_user_transform_with_all_values():
    user = create_test_user()

    result = transform_okta_user(user)

    expected = {
        "id": user.id,
        "activated": "01/01/2019, 00:00:01",
        "created": "01/01/2019, 00:00:01",
        "status_changed": "01/01/2019, 00:00:01",
        "last_login": "01/01/2019, 00:00:01",
        "okta_last_updated": "01/01/2019, 00:00:01",
        "password_changed": "01/01/2019, 00:00:01",
        "transition_to_status": user.transitioningToStatus,
        "login": user.profile.login,
        "email": user.profile.email,
        "last_name": user.profile.lastName,
        "first_name": user.profile.firstName,
    }

    assert result == expected


def test_userprofile_transform_with_no_activated():
    user = create_test_user()
    user.activated = None

    result = transform_okta_user(user)

    expected = {
        "id": user.id,
        "activated": None,
        "created": "01/01/2019, 00:00:01",
        "status_changed": "01/01/2019, 00:00:01",
        "last_login": "01/01/2019, 00:00:01",
        "okta_last_updated": "01/01/2019, 00:00:01",
        "password_changed": "01/01/2019, 00:00:01",
        "transition_to_status": user.transitioningToStatus,
        "login": user.profile.login,
        "email": user.profile.email,
        "last_name": user.profile.lastName,
        "first_name": user.profile.firstName,
    }

    assert result == expected


def test_userprofile_transform_with_no_status_changed():
    user = create_test_user()
    user.statusChanged = None

    result = transform_okta_user(user)

    expected = {
        "id": user.id,
        "activated": "01/01/2019, 00:00:01",
        "created": "01/01/2019, 00:00:01",
        "status_changed": None,
        "last_login": "01/01/2019, 00:00:01",
        "okta_last_updated": "01/01/2019, 00:00:01",
        "password_changed": "01/01/2019, 00:00:01",
        "transition_to_status": user.transitioningToStatus,
        "login": user.profile.login,
        "email": user.profile.email,
        "last_name": user.profile.lastName,
        "first_name": user.profile.firstName,
    }

    assert result == expected


def test_userprofile_transform_with_no_last_login():
    user = create_test_user()
    user.lastLogin = None

    result = transform_okta_user(user)

    expected = {
        "id": user.id,
        "activated": "01/01/2019, 00:00:01",
        "created": "01/01/2019, 00:00:01",
        "status_changed": "01/01/2019, 00:00:01",
        "last_login": None,
        "okta_last_updated": "01/01/2019, 00:00:01",
        "password_changed": "01/01/2019, 00:00:01",
        "transition_to_status": user.transitioningToStatus,
        "login": user.profile.login,
        "email": user.profile.email,
        "last_name": user.profile.lastName,
        "first_name": user.profile.firstName,
    }

    assert result == expected


def test_userprofile_transform_with_no_last_updated():
    user = create_test_user()
    user.lastUpdated = None

    result = transform_okta_user(user)

    expected = {
        "id": user.id,
        "activated": "01/01/2019, 00:00:01",
        "created": "01/01/2019, 00:00:01",
        "status_changed": "01/01/2019, 00:00:01",
        "last_login": "01/01/2019, 00:00:01",
        "okta_last_updated": None,
        "password_changed": "01/01/2019, 00:00:01",
        "transition_to_status": user.transitioningToStatus,
        "login": user.profile.login,
        "email": user.profile.email,
        "last_name": user.profile.lastName,
        "first_name": user.profile.firstName,
    }

    assert result == expected


def test_userprofile_transform_with_no_password_changed():
    user = create_test_user()
    user.passwordChanged = None

    result = transform_okta_user(user)

    expected = {
        "id": user.id,
        "activated": "01/01/2019, 00:00:01",
        "created": "01/01/2019, 00:00:01",
        "status_changed": "01/01/2019, 00:00:01",
        "last_login": "01/01/2019, 00:00:01",
        "okta_last_updated": "01/01/2019, 00:00:01",
        "password_changed": None,
        "transition_to_status": user.transitioningToStatus,
        "login": user.profile.login,
        "email": user.profile.email,
        "last_name": user.profile.lastName,
        "first_name": user.profile.firstName,
    }

    assert result == expected


def test_userprofile_transform_with_no_transition_status():
    user = create_test_user()
    user.transitioningToStatus = None

    result = transform_okta_user(user)

    expected = {
        "id": user.id,
        "activated": "01/01/2019, 00:00:01",
        "created": "01/01/2019, 00:00:01",
        "status_changed": "01/01/2019, 00:00:01",
        "last_login": "01/01/2019, 00:00:01",
        "okta_last_updated": "01/01/2019, 00:00:01",
        "password_changed": "01/01/2019, 00:00:01",
        "transition_to_status": None,
        "login": user.profile.login,
        "email": user.profile.email,
        "last_name": user.profile.lastName,
        "first_name": user.profile.firstName,
    }

    assert result == expected
