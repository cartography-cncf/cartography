from unittest.mock import MagicMock

from okta.models.user import User


def create_test_user():
    """Create a mock OktaUser object for testing."""
    user = MagicMock(spec=User)

    user.id = "userid"
    user.activated = "2019-01-01T00:00:01.000Z"
    user.created = "2019-01-01T00:00:01.000Z"
    user.status_changed = "2019-01-01T00:00:01.000Z"
    user.last_login = "2019-01-01T00:00:01.000Z"
    user.last_updated = "2019-01-01T00:00:01.000Z"
    user.password_changed = "2019-01-01T00:00:01.000Z"
    user.transitioning_to_status = "transition"

    # Status enum
    user.status = MagicMock()
    user.status.value = "ACTIVE"

    # Type
    user.type = MagicMock()
    user.type.id = "default_user_type"

    # Profile - using a mock with attribute access
    user.profile = MagicMock()
    user.profile.login = "test@lyft.com"
    user.profile.email = "test@lyft.com"
    user.profile.lastName = "LastName"
    user.profile.firstName = "firstName"
    user.profile.__dict__ = {
        "login": "test@lyft.com",
        "email": "test@lyft.com",
        "lastName": "LastName",
        "firstName": "firstName",
    }

    return user
