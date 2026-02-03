from unittest.mock import MagicMock

from okta.models.user import User


class MockUserProfile:
    """A mock profile object that properly supports __dict__ access."""

    def __init__(self):
        self.login = "test@lyft.com"
        self.email = "test@lyft.com"
        self.lastName = "LastName"
        self.firstName = "firstName"


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

    # Profile - using a real object for proper __dict__ support
    user.profile = MockUserProfile()

    return user
