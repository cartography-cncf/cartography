import logging
from unittest.mock import MagicMock

import pytest
import requests

import cartography.intel.airbyte.users
from tests.data.airbyte import multi_org
from tests.data.airbyte.fake_api import FakeAirbyteAPI
from tests.data.airbyte.fake_api import FORBIDDEN_DETAIL
from tests.data.airbyte.fake_api import make_client
from tests.data.airbyte.fake_api import TEST_ACCESS_TOKEN
from tests.data.airbyte.fake_api import TEST_CLIENT_SECRET

COMMON_JOB_PARAMETERS = {"UPDATE_TAG": 1, "ORG_ID": multi_org.ORG_ALPHA}


def _sync(api: FakeAirbyteAPI, neo4j_session: MagicMock) -> bool:
    return cartography.intel.airbyte.users.sync(
        neo4j_session,
        make_client(api),
        multi_org.ORG_ALPHA,
        COMMON_JOB_PARAMETERS,
    )


@pytest.mark.parametrize(
    "uri,params",
    [
        ("/users", {}),
        ("/permissions", {"userId": multi_org.SHARED_USER}),
    ],
)
def test_identity_denial_skips_load_and_cleanup(uri, params, caplog):
    # Arrange
    api = FakeAirbyteAPI()
    api.fail("GET", uri, 403, **params)
    neo4j_session = MagicMock()

    # Act
    with caplog.at_level(logging.WARNING):
        complete = _sync(api, neo4j_session)

    # Assert
    assert complete is False
    assert neo4j_session.mock_calls == []
    assert f"Airbyte denied GET {uri} for organization {multi_org.ORG_ALPHA}" in (
        caplog.text
    )
    assert "Organization Admin" in caplog.text
    for secret in (
        TEST_CLIENT_SECRET,
        TEST_ACCESS_TOKEN,
        FORBIDDEN_DETAIL,
        multi_org.SHARED_USER,
    ):
        assert secret not in caplog.text


@pytest.mark.parametrize("status", [401, 403])
def test_token_exchange_failure_is_raised(status):
    # Arrange
    api = FakeAirbyteAPI()
    api.fail("POST", "/applications/token", status)

    # Act and assert
    with pytest.raises(requests.HTTPError) as exc_info:
        _sync(api, MagicMock())
    assert exc_info.value.response.status_code == status
    assert [(method, uri) for method, uri, _ in api.requests] == [
        ("POST", "/applications/token"),
    ]


@pytest.mark.parametrize("uri", ["/users", "/permissions"])
@pytest.mark.parametrize("status", [400, 401, 404, 429, 500, 503])
def test_other_identity_http_errors_are_raised(uri, status):
    # Arrange
    api = FakeAirbyteAPI()
    api.fail("GET", uri, (status, {"status": status}))
    neo4j_session = MagicMock()

    # Act and assert
    with pytest.raises(requests.HTTPError) as exc_info:
        _sync(api, neo4j_session)
    assert exc_info.value.response.status_code == status
    assert neo4j_session.mock_calls == []


@pytest.mark.parametrize(
    "error",
    [requests.ConnectionError("connection reset"), requests.ReadTimeout("timed out")],
)
def test_transport_errors_are_raised(error):
    # Arrange
    api = FakeAirbyteAPI()
    api.fail("GET", "/permissions", error, userId=multi_org.SHARED_USER)

    # Act and assert
    with pytest.raises(type(error)):
        _sync(api, MagicMock())


def test_invalid_json_is_raised():
    # Arrange
    api = FakeAirbyteAPI()
    api.fail("GET", "/users", (200, b"<html>gateway</html>"))

    # Act and assert
    with pytest.raises(requests.JSONDecodeError):
        _sync(api, MagicMock())
