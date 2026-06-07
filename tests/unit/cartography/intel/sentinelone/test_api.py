import logging
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests

from cartography.intel.sentinelone.api import build_scope_params
from cartography.intel.sentinelone.api import call_sentinelone_api
from cartography.intel.sentinelone.api import get_paginated_results
from cartography.intel.sentinelone.api import is_retryable_sentinelone_exception
from cartography.intel.sentinelone.api import is_site_scope_http_error
from cartography.intel.sentinelone.api import SentinelOnePassthroughRequestException
from tests.data.sentinelone.api import EXPECTED_PAGINATED_RESULT
from tests.data.sentinelone.api import MOCK_API_RESPONSE_SUCCESS
from tests.data.sentinelone.api import MOCK_EMPTY_PAGINATION_RESPONSE
from tests.data.sentinelone.api import MOCK_PAGINATED_RESPONSE_PAGE_1
from tests.data.sentinelone.api import MOCK_PAGINATED_RESPONSE_PAGE_2
from tests.data.sentinelone.api import MOCK_SINGLE_PAGE_RESPONSE
from tests.data.sentinelone.api import TEST_API_TOKEN
from tests.data.sentinelone.api import TEST_API_URL
from tests.data.sentinelone.api import TEST_ENDPOINT
from tests.data.sentinelone.api import TEST_PARAMS


@patch("cartography.intel.sentinelone.api.requests.request")
def test_call_sentinelone_api_success(mock_request):
    """Test successful API call with default GET method"""
    mock_response = Mock()
    mock_response.json.return_value = MOCK_API_RESPONSE_SUCCESS
    mock_response.raise_for_status.return_value = None
    mock_request.return_value = mock_response

    result = call_sentinelone_api(TEST_API_URL, TEST_ENDPOINT, TEST_API_TOKEN)

    assert result == MOCK_API_RESPONSE_SUCCESS
    mock_request.assert_called_once_with(
        method="GET",
        url=f"{TEST_API_URL}/{TEST_ENDPOINT}",
        headers={
            "Accept": "application/json",
            "Authorization": f"ApiToken {TEST_API_TOKEN}",
            "Content-Type": "application/json",
        },
        params=None,
        json=None,
        timeout=(60, 60),
    )


@patch("cartography.intel.sentinelone.api.requests.request")
def test_call_sentinelone_api_with_params(mock_request):
    """Test API call with query parameters"""
    mock_response = Mock()
    mock_response.json.return_value = MOCK_API_RESPONSE_SUCCESS
    mock_response.raise_for_status.return_value = None
    mock_request.return_value = mock_response

    result = call_sentinelone_api(
        TEST_API_URL, TEST_ENDPOINT, TEST_API_TOKEN, params=TEST_PARAMS
    )

    assert result == MOCK_API_RESPONSE_SUCCESS
    mock_request.assert_called_once_with(
        method="GET",
        url=f"{TEST_API_URL}/{TEST_ENDPOINT}",
        headers={
            "Accept": "application/json",
            "Authorization": f"ApiToken {TEST_API_TOKEN}",
            "Content-Type": "application/json",
        },
        params=TEST_PARAMS,
        json=None,
        timeout=(60, 60),
    )


@patch("time.sleep")
@patch("cartography.intel.sentinelone.api.requests.request")
def test_call_sentinelone_api_http_error(mock_request, mock_sleep):
    """Test non-retryable HTTP errors fail immediately."""
    mock_response = Mock()
    mock_response.status_code = 401
    http_error = requests.exceptions.HTTPError("HTTP 401 Error", response=mock_response)
    mock_response.raise_for_status.side_effect = http_error
    mock_request.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError):
        call_sentinelone_api(TEST_API_URL, TEST_ENDPOINT, TEST_API_TOKEN)

    assert mock_request.call_count == 1
    mock_sleep.assert_not_called()


@patch("time.sleep")
@patch("cartography.intel.sentinelone.api.requests.request")
def test_call_sentinelone_api_site_scope_http_error_avoids_backoff_giveup_log(
    mock_request,
    mock_sleep,
    caplog,
):
    """Expected site-scope 403s should not emit backoff error logs."""
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.json.return_value = {
        "errors": [
            {
                "code": 4030010,
                "detail": "Action is not allowed to site users",
            },
        ],
    }
    http_error = requests.exceptions.HTTPError("HTTP 403 Error", response=mock_response)
    mock_response.raise_for_status.side_effect = http_error
    mock_request.return_value = mock_response

    with caplog.at_level(logging.INFO, logger="backoff"):
        with pytest.raises(requests.exceptions.HTTPError):
            call_sentinelone_api(
                TEST_API_URL,
                TEST_ENDPOINT,
                TEST_API_TOKEN,
                passthrough_exceptions=is_site_scope_http_error,
            )

    assert "Giving up request_once" not in caplog.text
    assert "Backing off request_once" not in caplog.text
    mock_sleep.assert_not_called()


@patch("cartography.intel.sentinelone.api.requests.request")
def test_call_sentinelone_api_passthrough_reraises_original_http_error(mock_request):
    """Passthrough exceptions should bypass backoff and preserve the original error."""
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.json.return_value = {
        "errors": [
            {
                "code": 4030010,
                "detail": "Action is not allowed to site users",
            },
        ],
    }
    http_error = requests.exceptions.HTTPError("HTTP 403 Error", response=mock_response)
    mock_response.raise_for_status.side_effect = http_error
    mock_request.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError) as excinfo:
        call_sentinelone_api(
            TEST_API_URL,
            TEST_ENDPOINT,
            TEST_API_TOKEN,
            passthrough_exceptions=is_site_scope_http_error,
        )

    assert excinfo.value is http_error


def test_passthrough_request_exception_wraps_original_request_error():
    http_error = requests.exceptions.HTTPError("HTTP 403 Error")

    wrapped = SentinelOnePassthroughRequestException(http_error)

    assert wrapped.original is http_error


@patch("time.sleep")
@patch("cartography.intel.sentinelone.api.requests.request")
def test_call_sentinelone_api_retries_transient_http_error(mock_request, mock_sleep):
    """Test retryable HTTP errors are retried."""
    error_response = Mock()
    error_response.status_code = 503
    transient_error = requests.exceptions.HTTPError(
        "HTTP 503 Error",
        response=error_response,
    )
    success_response = Mock()
    success_response.json.return_value = MOCK_API_RESPONSE_SUCCESS
    success_response.raise_for_status.return_value = None

    first_response = Mock()
    first_response.raise_for_status.side_effect = transient_error

    mock_request.side_effect = [first_response, success_response]

    result = call_sentinelone_api(TEST_API_URL, TEST_ENDPOINT, TEST_API_TOKEN)

    assert result == MOCK_API_RESPONSE_SUCCESS
    assert mock_request.call_count == 2
    mock_sleep.assert_called_once()


@patch("cartography.intel.sentinelone.api.call_sentinelone_api")
def test_get_paginated_results_single_page(mock_api_call):
    """Test pagination with single page response"""
    mock_api_call.return_value = MOCK_SINGLE_PAGE_RESPONSE

    result = get_paginated_results(TEST_API_URL, TEST_ENDPOINT, TEST_API_TOKEN)

    assert result == MOCK_SINGLE_PAGE_RESPONSE["data"]
    mock_api_call.assert_called_once_with(
        api_url=TEST_API_URL,
        endpoint=TEST_ENDPOINT,
        api_token=TEST_API_TOKEN,
        params={"limit": 100},
    )


@patch("cartography.intel.sentinelone.api.call_sentinelone_api")
def test_get_paginated_results_multiple_pages(mock_api_call):
    """Test pagination with multiple pages"""
    mock_api_call.side_effect = [
        MOCK_PAGINATED_RESPONSE_PAGE_1,
        MOCK_PAGINATED_RESPONSE_PAGE_2,
    ]

    result = get_paginated_results(TEST_API_URL, TEST_ENDPOINT, TEST_API_TOKEN)

    assert result == EXPECTED_PAGINATED_RESULT
    assert mock_api_call.call_count == 2

    # Verify both calls were made with correct base parameters
    for call in mock_api_call.call_args_list:
        assert call[1]["api_url"] == TEST_API_URL
        assert call[1]["endpoint"] == TEST_ENDPOINT
        assert call[1]["api_token"] == TEST_API_TOKEN
        assert "limit" in call[1]["params"]


@patch("cartography.intel.sentinelone.api.call_sentinelone_api")
def test_get_paginated_results_empty_response(mock_api_call):
    """Test pagination with empty response"""
    mock_api_call.return_value = MOCK_EMPTY_PAGINATION_RESPONSE

    result = get_paginated_results(TEST_API_URL, TEST_ENDPOINT, TEST_API_TOKEN)

    assert result == []
    mock_api_call.assert_called_once()


@patch("cartography.intel.sentinelone.api.call_sentinelone_api")
def test_get_paginated_results_with_params(mock_api_call):
    """Test pagination with custom parameters"""
    mock_api_call.return_value = MOCK_SINGLE_PAGE_RESPONSE

    result = get_paginated_results(
        TEST_API_URL, TEST_ENDPOINT, TEST_API_TOKEN, params=TEST_PARAMS
    )

    assert result == MOCK_SINGLE_PAGE_RESPONSE["data"]
    mock_api_call.assert_called_once_with(
        api_url=TEST_API_URL,
        endpoint=TEST_ENDPOINT,
        api_token=TEST_API_TOKEN,
        params=TEST_PARAMS,
    )


def test_build_scope_params_account_scope():
    assert build_scope_params(account_id="account-123") == {"accountIds": "account-123"}


def test_build_scope_params_site_scope_takes_precedence():
    assert build_scope_params(account_id="account-123", site_id="site-123") == {
        "siteIds": "site-123",
    }


def test_is_site_scope_http_error():
    response = Mock()
    response.status_code = 403
    response.json.return_value = {
        "errors": [
            {
                "code": 4030010,
                "detail": "Action is not allowed to site users",
            },
        ],
    }
    exc = requests.exceptions.HTTPError(response=response)

    assert is_site_scope_http_error(exc) is True


def test_is_site_scope_http_error_false_for_other_http_errors():
    response = Mock()
    response.status_code = 403
    response.json.return_value = {"errors": [{"code": 4030001, "detail": "Forbidden"}]}
    exc = requests.exceptions.HTTPError(response=response)

    assert is_site_scope_http_error(exc) is False


def test_is_site_scope_http_error_false_for_non_dict_payload():
    response = Mock()
    response.status_code = 403
    response.json.return_value = ["unexpected"]
    exc = requests.exceptions.HTTPError(response=response)

    assert is_site_scope_http_error(exc) is False


def test_is_site_scope_http_error_false_for_non_dict_errors():
    response = Mock()
    response.status_code = 403
    response.json.return_value = {"errors": ["unexpected"]}
    exc = requests.exceptions.HTTPError(response=response)

    assert is_site_scope_http_error(exc) is False


def test_is_retryable_sentinelone_exception():
    response = Mock()
    response.status_code = 429
    http_error = requests.exceptions.HTTPError(response=response)

    assert is_retryable_sentinelone_exception(http_error) is True
    assert is_retryable_sentinelone_exception(requests.exceptions.Timeout()) is True
    assert (
        is_retryable_sentinelone_exception(requests.exceptions.ConnectionError())
        is True
    )


def test_is_retryable_sentinelone_exception_false_for_non_transient_http_error():
    response = Mock()
    response.status_code = 403
    http_error = requests.exceptions.HTTPError(response=response)

    assert is_retryable_sentinelone_exception(http_error) is False
