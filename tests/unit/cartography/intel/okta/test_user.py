from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.okta.users import _get_okta_users
from cartography.intel.okta.users import transform_okta_user
from tests.data.okta.users import create_test_user


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


def _make_paged_result(users, has_next=False, next_url=None):
    """Helper to create a mock PagedResults object."""
    mock = MagicMock()
    mock.result = users
    mock.response.links = {}
    if has_next and next_url:
        mock.response.links["next"] = {"url": next_url}
    mock.response.headers = {
        "x-rate-limit-remaining": "100",
        "x-rate-limit-limit": "100",
        "x-rate-limit-reset": "0",
    }
    return mock


@patch("cartography.intel.okta.users.check_rate_limit")
def test_get_okta_users_fetches_all_pages(mock_rate_limit):
    """Verify that _get_okta_users fetches every page including the last one."""
    user_page_1 = [create_test_user()]
    user_page_2 = [create_test_user()]
    user_page_3 = [create_test_user()]

    page_3 = _make_paged_result(user_page_3, has_next=False)
    page_2 = _make_paged_result(
        user_page_2, has_next=True, next_url="https://okta.example.com/page3"
    )
    page_1 = _make_paged_result(
        user_page_1, has_next=True, next_url="https://okta.example.com/page2"
    )

    mock_client = MagicMock()
    mock_client.get_paged_users.side_effect = [page_1, page_2, page_3]

    result = _get_okta_users(mock_client)

    assert len(result) == 3
    assert result == user_page_1 + user_page_2 + user_page_3
    assert mock_client.get_paged_users.call_count == 3


@patch("cartography.intel.okta.users.check_rate_limit")
def test_get_okta_users_single_page(mock_rate_limit):
    """Verify single-page results are returned correctly."""
    users = [create_test_user()]
    page = _make_paged_result(users, has_next=False)

    mock_client = MagicMock()
    mock_client.get_paged_users.return_value = page

    result = _get_okta_users(mock_client)

    assert len(result) == 1
    assert mock_client.get_paged_users.call_count == 1
