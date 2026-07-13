from unittest.mock import MagicMock
from unittest.mock import patch

from kiota_abstractions.api_error import APIError
from kiota_http.middleware import RetryHandler

from cartography.intel.microsoft.client import create_graph_service_client
from cartography.intel.microsoft.client import get_api_error_response_header
from cartography.intel.microsoft.client import GRAPH_EXTRA_RETRY_STATUS_CODES
from cartography.intel.microsoft.client import GRAPH_MAX_RETRIES
from cartography.intel.microsoft.client import GRAPH_RETRY_DELAY_SECONDS
from cartography.intel.microsoft.client import GRAPH_SCOPES


@patch("cartography.intel.microsoft.client.GraphServiceClient")
@patch("cartography.intel.microsoft.client.GraphRequestAdapter")
@patch(
    "cartography.intel.microsoft.client.GraphClientFactory.create_with_custom_middleware"
)
@patch("cartography.intel.microsoft.client.AzureIdentityAuthenticationProvider")
def test_create_graph_service_client_configures_retry_middleware(
    mock_auth_provider,
    mock_create_with_custom_middleware,
    mock_graph_request_adapter,
    mock_graph_service_client,
):
    credential = object()
    http_client = MagicMock()
    request_adapter = MagicMock()

    mock_create_with_custom_middleware.return_value = http_client
    mock_graph_request_adapter.return_value = request_adapter

    create_graph_service_client(credential)

    mock_auth_provider.assert_called_once_with(credential, scopes=GRAPH_SCOPES)
    mock_graph_request_adapter.assert_called_once_with(
        mock_auth_provider.return_value,
        client=http_client,
    )
    mock_graph_service_client.assert_called_once_with(request_adapter=request_adapter)

    middleware = mock_create_with_custom_middleware.call_args.args[0]
    retry_handler = next(m for m in middleware if isinstance(m, RetryHandler))
    assert retry_handler.options.max_retry == GRAPH_MAX_RETRIES
    assert retry_handler.options.max_delay == GRAPH_RETRY_DELAY_SECONDS
    # transient Graph 500/502 are retried on top of kiota's default 429/503/504
    assert GRAPH_EXTRA_RETRY_STATUS_CODES <= retry_handler.retry_on_status_codes
    assert {429, 503, 504} <= retry_handler.retry_on_status_codes


def test_get_api_error_response_header_is_case_insensitive():
    error = APIError(
        response_status_code=429,
        response_headers={
            "Retry-After": "17",
            "request-id": "req-123",
            "X-MS-Throttle-Information": "ResourceUnitLimitExceeded",
        },
    )

    assert get_api_error_response_header(error, "retry-after") == "17"
    assert get_api_error_response_header(error, "Request-Id") == "req-123"
    assert (
        get_api_error_response_header(error, "x-ms-throttle-information")
        == "ResourceUnitLimitExceeded"
    )
    assert get_api_error_response_header(error, "x-ms-throttle-scope") is None
