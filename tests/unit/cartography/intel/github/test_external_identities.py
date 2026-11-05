import json
from copy import deepcopy
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from unittest.mock import call
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests

from cartography.intel.github.external_identities import get_external_identities
from cartography.intel.github.external_identities import sync
from cartography.intel.github.external_identities import transform_external_identities
from cartography.intel.github.users import transform_users as transform_github_users
from cartography.intel.ontology.users import transform_users
from tests.data.github.external_identities import API_URL
from tests.data.github.external_identities import FORBIDDEN
from tests.data.github.external_identities import IDENTITIES
from tests.data.github.external_identities import NO_SAML_PROVIDER
from tests.data.github.external_identities import ORG
from tests.data.github.external_identities import ORG_URL
from tests.data.github.external_identities import page
from tests.data.github.rate_limit import RATE_LIMIT_RESPONSE_JSON


@pytest.fixture(autouse=True)
def deterministic_jitter():
    with patch("cartography.intel.github.util.random.random", return_value=0):
        yield


@pytest.fixture(autouse=True)
def available_rate_limit():
    response = deepcopy(RATE_LIMIT_RESPONSE_JSON)
    response["resources"]["graphql"]["remaining"] = 5000
    with patch("cartography.intel.github.util.requests.get") as mock_get:
        mock_get.return_value.json.return_value = response
        yield mock_get


def test_transform_preserves_nameid_and_nullable_fields():
    # Arrange
    identities = deepcopy(IDENTITIES)
    identities[1]["samlIdentity"]["nameId"] = "opaque-id-123"

    # Act
    result = transform_external_identities(identities, ORG_URL)

    # Assert
    assert result == [
        {
            "id": f"{ORG_URL}|E_example_alice",
            "saml_name_id": " Alice@Example.com ",
            "saml_name_id_normalized": "alice@example.com",
            "user_url": "https://github.com/example-alice",
        },
        {
            "id": f"{ORG_URL}|E_example_bob",
            "saml_name_id": "opaque-id-123",
            "saml_name_id_normalized": "opaque-id-123",
            "user_url": "https://github.com/example-bob",
        },
        {
            "id": f"{ORG_URL}|E_example_unlinked",
            "saml_name_id": "unlinked@example.com",
            "saml_name_id_normalized": "unlinked@example.com",
            "user_url": None,
        },
        {
            "id": f"{ORG_URL}|E_example_without_saml",
            "saml_name_id": None,
            "saml_name_id_normalized": None,
            "user_url": "https://github.com/example-carol",
        },
    ]
    assert identities[0] == IDENTITIES[0]
    assert (
        transform_external_identities(
            identities, "https://github.example.com/example-org"
        )[0]["id"]
        != result[0]["id"]
    )


@patch("cartography.intel.github.util.requests.post")
def test_get_paginates(mock_post):
    # Arrange
    mock_post.side_effect = [
        Mock(json=lambda: page(IDENTITIES[:2], has_next_page=True, cursor="cursor-1")),
        Mock(json=lambda: page(IDENTITIES[2:])),
    ]

    # Act
    result = get_external_identities("test-token", API_URL, ORG)

    # Assert
    assert result == (IDENTITIES, ORG_URL)
    assert [
        json.loads(call.kwargs["json"]["variables"])
        for call in mock_post.call_args_list
    ] == [
        {"login": ORG, "cursor": None},
        {"login": ORG, "cursor": "cursor-1"},
    ]


@pytest.mark.parametrize(
    "response,expected",
    [(NO_SAML_PROVIDER, None), (page([]), ([], ORG_URL)), (FORBIDDEN, None)],
)
@patch("cartography.intel.github.util.requests.post")
def test_get_distinguishes_absence_from_denied_access(mock_post, response, expected):
    # Arrange
    mock_post.return_value.json.return_value = response

    # Act
    result = get_external_identities("test-token", API_URL, ORG)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "error",
    [
        {"message": "timedout"},
        {"type": "RATE_LIMITED", "message": "API rate limit exceeded"},
    ],
)
@patch("cartography.intel.github.util.time.sleep")
@patch("cartography.intel.github.util.requests.post")
def test_get_rejects_partial_graphql_results(mock_post, mock_sleep, error):
    # Arrange
    response = page(IDENTITIES)
    response["errors"] = [error]
    mock_post.return_value.json.return_value = response

    # Act and assert
    with pytest.raises(RuntimeError, match="query failed"):
        get_external_identities("test-token", API_URL, ORG)
    assert mock_post.call_count == 5
    assert mock_sleep.call_count == 4


@patch("cartography.intel.github.util.requests.post")
def test_get_propagates_http_failure(mock_post):
    # Arrange
    mock_post.return_value.raise_for_status.side_effect = requests.HTTPError("401")

    # Act and assert
    with pytest.raises(requests.HTTPError):
        get_external_identities("test-token", API_URL, ORG)


@patch("cartography.intel.github.util.requests.post")
def test_get_rejects_nonadvancing_pagination(mock_post):
    # Arrange
    mock_post.return_value.json.return_value = page(
        IDENTITIES, has_next_page=True, cursor="same-cursor"
    )

    # Act and assert
    with pytest.raises(RuntimeError, match="did not advance"):
        get_external_identities("test-token", API_URL, ORG)
    assert mock_post.call_count == 2


def _http_response(status, headers=None, payload=None):
    response = requests.Response()
    response.status_code = status
    response.headers.update(headers or {})
    response._content = json.dumps(payload or {}).encode()
    return response


@pytest.mark.parametrize(
    "failure,delay",
    [
        *[(_http_response(status), 2) for status in (408, 500, 502, 503, 504)],
        (_http_response(429, {"retry-after": "7"}), 7),
        (_http_response(429, {"retry-after": "301"}), 301),
        (_http_response(403, {"retry-after": "8"}), 8),
        (_http_response(403, payload={"message": "secondary rate limit"}), 60),
        (requests.Timeout(), 2),
        (requests.ConnectionError(), 2),
        (requests.exceptions.ChunkedEncodingError(), 2),
    ],
)
@patch("cartography.intel.github.util.time.sleep")
@patch("cartography.intel.github.util.requests.post")
def test_get_retries_transport_failure_on_same_page(
    mock_post, mock_sleep, failure, delay
):
    # Arrange
    mock_post.side_effect = [
        _http_response(
            200, payload=page(IDENTITIES[:2], has_next_page=True, cursor="cursor-1")
        ),
        failure,
        _http_response(200, payload=page(IDENTITIES[2:])),
    ]

    # Act
    result = get_external_identities("test-token", API_URL, ORG)

    # Assert
    assert result == (IDENTITIES, ORG_URL)
    assert [
        json.loads(c.kwargs["json"]["variables"])["cursor"]
        for c in mock_post.call_args_list
    ] == [None, "cursor-1", "cursor-1"]
    mock_sleep.assert_called_once_with(delay)


@patch("cartography.intel.github.util.time.sleep")
@patch("cartography.intel.github.util.requests.post")
def test_get_recovers_partial_graphql_page_without_duplicate_records(
    mock_post, mock_sleep
):
    # Arrange
    limited = page(IDENTITIES[:1])
    limited["errors"] = [{"type": "RATE_LIMITED", "message": "API rate limit exceeded"}]
    timed_out = page(IDENTITIES[:1])
    timed_out["errors"] = [{"message": "timedout"}]
    mock_post.side_effect = [
        _http_response(200, payload=limited),
        _http_response(
            200, payload=page(IDENTITIES[:2], has_next_page=True, cursor="cursor-1")
        ),
        _http_response(200, payload=timed_out),
        _http_response(200, payload=page(IDENTITIES[2:])),
    ]

    # Act
    result = get_external_identities("test-token", API_URL, ORG)

    # Assert
    assert result == (IDENTITIES, ORG_URL)
    assert mock_sleep.call_args_list == [call(60), call(2)]
    assert [
        json.loads(c.kwargs["json"]["variables"])["cursor"]
        for c in mock_post.call_args_list
    ] == [None, None, "cursor-1", "cursor-1"]


@pytest.mark.parametrize("status,headers", [(401, {}), (403, {}), (404, {})])
@patch("cartography.intel.github.util.time.sleep")
@patch("cartography.intel.github.util.requests.post")
def test_get_does_not_retry_permanent_failure(mock_post, mock_sleep, status, headers):
    # Arrange
    mock_post.return_value = _http_response(status, headers)

    # Act and assert
    with pytest.raises(requests.HTTPError):
        get_external_identities("test-token", API_URL, ORG)
    mock_post.assert_called_once()
    mock_sleep.assert_not_called()


@patch("cartography.intel.github.util.time.sleep")
@patch("cartography.intel.github.util.requests.post")
def test_get_bounds_transport_attempts(mock_post, mock_sleep):
    # Arrange
    mock_post.return_value = _http_response(503)

    # Act and assert
    with pytest.raises(requests.HTTPError):
        get_external_identities("test-token", API_URL, ORG)
    assert mock_post.call_count == 5
    assert mock_sleep.call_args_list == [call(2), call(4), call(8), call(16)]


@patch("cartography.intel.github.util.time.sleep")
@patch("cartography.intel.github.util.requests.post")
def test_get_does_not_retry_unknown_graphql_errors(mock_post, mock_sleep):
    # Arrange
    mock_post.return_value = _http_response(
        200,
        payload={
            "errors": [
                {"type": "NOT_FOUND", "message": "Could not resolve organization"}
            ]
        },
    )

    # Act and assert
    with pytest.raises(RuntimeError, match="query failed"):
        get_external_identities("test-token", API_URL, ORG)
    mock_post.assert_called_once()
    mock_sleep.assert_not_called()


@pytest.mark.parametrize(
    "value,expected",
    [
        (" Alice@Example.com ", "alice@example.com"),
        ("\tAlice@Example.com\n", "alice@example.com"),
        ("\u00a0Alice@Example.com\u00a0", "alice@example.com"),
        ("\u202fAlice@Example.com\u202f", "alice@example.com"),
        ("\u0085Alice@Example.com\u0085", "alice@example.com"),
        ("\u0130@Example.com", "i\u0307@example.com"),
        (None, None),
        ("", None),
        (" \u00a0\u202f\u0085", None),
    ],
)
def test_identity_sources_share_normalization_policy(value, expected):
    # Arrange
    identity = deepcopy(IDENTITIES[0])
    identity["samlIdentity"]["nameId"] = value

    # Act
    github = transform_external_identities([identity], ORG_URL)[0]
    canonical = transform_users([{"email": value}])[0]
    members, owners = transform_github_users(
        [
            {
                "node": {
                    "url": "member",
                    "email": value,
                    "organizationVerifiedDomainEmails": [value],
                },
                "role": "MEMBER",
                "hasTwoFactorEnabled": True,
            }
        ],
        [
            {
                "node": {
                    "url": "owner",
                    "email": value,
                    "organizationVerifiedDomainEmails": [value],
                },
                "organizationRole": "UNAFFILIATED",
            }
        ],
        {"url": ORG_URL},
    )

    # Assert
    for user in members + owners:
        assert user["normalized_emails"] == ([expected] if expected else [])
        assert user["organizationVerifiedDomainEmails"] == [value]
    assert github["saml_name_id_normalized"] == expected
    assert canonical["normalized_email"] == expected
    assert github["saml_name_id"] == canonical["email"] == value
    assert identity["samlIdentity"]["nameId"] == value


@pytest.mark.parametrize("graphql_error", [False, True])
@patch("cartography.intel.github.util.datetime")
@patch("cartography.intel.github.util.time.sleep")
@patch("cartography.intel.github.util.requests.post")
def test_get_waits_for_primary_reset(
    mock_post, mock_sleep, mock_datetime, available_rate_limit, graphql_error
):
    # Arrange
    now = datetime(2040, 1, 1, tzinfo=timezone.utc)
    mock_datetime.now.return_value = now
    mock_datetime.fromtimestamp = datetime.fromtimestamp
    reset = int((now + timedelta(minutes=47)).timestamp())
    if graphql_error:
        failure = _http_response(200, payload={"errors": [{"type": "RATE_LIMITED"}]})
        healthy = deepcopy(available_rate_limit.return_value.json.return_value)
        exhausted = deepcopy(healthy)
        exhausted["resources"]["graphql"].update(remaining=0, reset=reset)
        available_rate_limit.side_effect = [
            _http_response(200, payload=healthy),
            _http_response(200, payload=exhausted),
        ]
    else:
        failure = _http_response(
            403, {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(reset)}
        )
    mock_post.side_effect = [failure, _http_response(200, payload=page(IDENTITIES))]

    # Act
    result = get_external_identities("test-token", API_URL, ORG)

    # Assert
    assert result == (IDENTITIES, ORG_URL)
    assert available_rate_limit.call_count == 2
    assert mock_sleep.call_args_list == (
        [call(60), call(48 * 60)] if graphql_error else [call(48 * 60)]
    )
    assert mock_post.call_args_list[0] == mock_post.call_args_list[1]


@patch("cartography.intel.github.util.time.sleep")
@patch("cartography.intel.github.util.requests.post")
def test_secondary_rate_limit_backs_off_exponentially(mock_post, mock_sleep):
    # Arrange
    mock_post.return_value = _http_response(
        403, payload={"message": "secondary rate limit"}
    )

    # Act and assert
    with pytest.raises(requests.HTTPError):
        get_external_identities("test-token", API_URL, ORG)
    assert mock_sleep.call_args_list == [call(60), call(120), call(240), call(480)]
    assert mock_post.call_count == 5


@patch("cartography.intel.github.external_identities.load")
@patch("cartography.intel.github.util.requests.post")
def test_sync_does_not_swallow_graph_write_failure(mock_post, mock_load):
    # Arrange
    mock_post.return_value = _http_response(200, payload=page(IDENTITIES))
    mock_load.side_effect = RuntimeError("database unavailable")

    # Act and assert
    with pytest.raises(RuntimeError, match="database unavailable"):
        sync(Mock(), {"UPDATE_TAG": 100}, "test-token", API_URL, ORG)
