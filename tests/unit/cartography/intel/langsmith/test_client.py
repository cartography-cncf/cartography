from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests
from urllib3.exceptions import ConnectTimeoutError
from urllib3.exceptions import MaxRetryError
from urllib3.exceptions import ResponseError

from cartography.intel.langsmith.util import _build_assistant_session
from cartography.intel.langsmith.util import _request_failure_reason
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


@pytest.mark.parametrize(
    "error, expected",
    [
        (
            requests.ConnectionError(
                MaxRetryError(None, "/assistants/search", ConnectTimeoutError("slow"))
            ),
            "ConnectTimeoutError",
        ),
        (
            requests.exceptions.RetryError(
                MaxRetryError(None, "/assistants/search", ResponseError("too many 503"))
            ),
            "repeated 429/5xx",
        ),
        (requests.ReadTimeout("read timed out"), "ReadTimeout"),
    ],
)
def test_assistant_search_failures_are_named_by_root_cause(error, expected):
    # Act and assert
    assert _request_failure_reason(error) == expected


def test_an_unreachable_deployment_is_not_retried():
    # Arrange
    session = _build_assistant_session()

    # Act
    retry = session.get_adapter("https://dep.example").max_retries

    # Assert
    # A deployment that does not accept a connection within the timeout will not on a
    # retry either; retrying only stretches the slowest worker.
    assert retry.connect == 0
    assert retry.read == 0
