from unittest.mock import MagicMock

from okta.models.user import User
from okta.models.user_profile import UserProfile


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

    # Profile — use the real pydantic model so the transform exercises
    # model_dump() / additional_properties flattening end-to-end.
    user.profile = UserProfile(
        login="test@lyft.com",
        email="test@lyft.com",
        last_name="LastName",
        first_name="firstName",
    )

    return user
