from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests

from cartography.intel.langsmith.util import LangSmithClient
from cartography.intel.langsmith.util import LangSmithFetchError


def _client() -> LangSmithClient:
    return LangSmithClient(
        "lsv2_pt_fake", "https://api.example", "https://host.example"
    )


def _response(status_code: int, body=None) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = body
    return response


@pytest.mark.parametrize(
    "outcome, expected_not_found",
    [
        (_response(404), True),
        (_response(403), False),
        (_response(401), False),
        (requests.ReadTimeout("read timed out"), False),
        (requests.ConnectionError("connection refused"), False),
        # What requests raises once 429/5xx retries are exhausted.
        (requests.exceptions.RetryError("too many 503 error responses"), False),
    ],
)
def test_unreadable_listing_reports_whether_it_is_empty(outcome, expected_not_found):
    # Arrange
    client = _client()

    # Act
    with patch.object(requests.Session, "get", side_effect=[outcome]):
        with pytest.raises(LangSmithFetchError) as raised:
            client.get("/api/v1/orgs/current/roles")

    # Assert
    assert raised.value.not_found is expected_not_found


def test_envelope_without_its_rows_fails_rather_than_reading_empty():
    # Arrange
    client = _client()
    malformed = _response(200, {"offset": 0})

    # Act and assert
    with patch.object(requests.Session, "get", return_value=malformed):
        with pytest.raises(KeyError):
            client.get_paginated_envelope("/v2/deployments", key="resources")
