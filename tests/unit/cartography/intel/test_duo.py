import pytest

from cartography.intel.duo.endpoints import _transform_endpoints
from cartography.intel.duo.users import _transform_users
from tests.data.duo.endpoints import GET_ENDPOINTS_RESPONSE
from tests.data.duo.users import GET_USERS_RESPONSE


@pytest.mark.parametrize(
    "transform, payload",
    [
        (_transform_users, GET_USERS_RESPONSE[0]),
        (_transform_endpoints, GET_ENDPOINTS_RESPONSE[0]),
    ],
    ids=["users", "endpoints"],
)
@pytest.mark.parametrize(
    "email",
    ["Alice@Example.com", " Alice@Example.com ", "\tAlice@Example.com\u00a0"],
)
def test_transform_preserves_nonblank_email(transform, payload, email):
    # Arrange
    source = {**payload, "email": email}

    # Act
    transformed = transform([source])

    # Assert
    assert {row["email"] for row in transformed} == {email}
