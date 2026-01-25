from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests

from cartography.intel.sentinelone.api import call_sentinelone_api
from cartography.intel.sentinelone.api import get_paginated_results
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
    """Test API call with HTTP error"""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "HTTP 401 Error"
    )
    mock_request.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError):
        call_sentinelone_api(TEST_API_URL, TEST_ENDPOINT, TEST_API_TOKEN)


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
