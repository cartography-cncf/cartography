from unittest.mock import MagicMock

import pytest
import requests

import cartography.intel.airbyte.users
from tests.data.airbyte import multi_org
from tests.data.airbyte.fake_api import FakeAirbyteAPI
from tests.data.airbyte.fake_api import make_client


@pytest.mark.parametrize(
    "method,uri,result,expected",
    [
        # AirbyteClient.get() exchanges the token first, inside the same call.
        ("POST", "/applications/token", 401, requests.HTTPError),
        ("POST", "/applications/token", 403, requests.HTTPError),
        ("GET", "/users", 401, requests.HTTPError),
        ("GET", "/permissions", 429, requests.HTTPError),
        ("GET", "/users", 503, requests.HTTPError),
        (
            "GET",
            "/permissions",
            requests.ConnectionError("reset"),
            requests.ConnectionError,
        ),
        ("GET", "/users", (200, b"<html>gateway</html>"), requests.JSONDecodeError),
    ],
)
def test_failures_other_than_an_identity_denial_are_raised(
    method, uri, result, expected
):
    # Arrange
    api = FakeAirbyteAPI()
    api.fail(method, uri, result)

    # Act and assert
    with pytest.raises(expected):
        cartography.intel.airbyte.users.sync(
            MagicMock(),
            make_client(api),
            multi_org.ORG_ALPHA,
            {"UPDATE_TAG": 1, "ORG_ID": multi_org.ORG_ALPHA},
        )
