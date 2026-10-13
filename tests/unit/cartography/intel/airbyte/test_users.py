from unittest.mock import MagicMock

import pytest
import requests

import cartography.intel.airbyte.users
from tests.data.airbyte.fake_api import FakeAirbyteAPI
from tests.data.airbyte.fake_api import make_client
from tests.data.airbyte.multi_org import ORG_ALPHA


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
    neo4j_session = MagicMock()
    api = FakeAirbyteAPI()
    api.fail(method, uri, result)

    # Act and assert
    with pytest.raises(expected):
        cartography.intel.airbyte.users.sync(
            neo4j_session,
            make_client(api),
            ORG_ALPHA,
            {"UPDATE_TAG": 1, "ORG_ID": ORG_ALPHA},
        )

    # Assert: the error is raised before anything is written to the graph.
    assert neo4j_session.method_calls == []
