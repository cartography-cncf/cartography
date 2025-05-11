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
