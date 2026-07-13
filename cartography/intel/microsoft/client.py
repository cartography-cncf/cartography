from collections.abc import Mapping
from typing import Any

from kiota_abstractions.api_error import APIError
from kiota_authentication_azure.azure_identity_authentication_provider import (
    AzureIdentityAuthenticationProvider,
)
from kiota_http.kiota_client_factory import KiotaClientFactory
from kiota_http.middleware import RetryHandler
from kiota_http.middleware.options.retry_handler_option import RetryHandlerOption
from msgraph import GraphServiceClient
from msgraph.graph_request_adapter import GraphRequestAdapter
from msgraph.graph_request_adapter import options as graph_request_adapter_options
from msgraph_core import GraphClientFactory
from msgraph_core.middleware import GraphTelemetryHandler
from msgraph_core.middleware.options import GraphTelemetryHandlerOption

GRAPH_SCOPES = ["https://graph.microsoft.com/.default"]
GRAPH_RETRY_DELAY_SECONDS = 5.0
GRAPH_MAX_RETRIES = 6
# kiota's RetryHandler only retries {429, 503, 504} out of the box, but Graph
# also emits transient 500/502 ("UnknownError") that strand a sync. Add them so
# every Graph call retries them (RetryHandlerOption exposes no status-code hook).
GRAPH_EXTRA_RETRY_STATUS_CODES = frozenset({500, 502})


def create_graph_service_client(credentials: Any) -> GraphServiceClient:
    retry_option = RetryHandlerOption(
        delay=GRAPH_RETRY_DELAY_SECONDS,
        max_retries=GRAPH_MAX_RETRIES,
    )
    options = {
        **graph_request_adapter_options,
        RetryHandlerOption.get_key(): retry_option,
    }
    # Rebuild the default middleware so we can widen the retry status codes, then
    # re-append the telemetry handler that create_with_default_middleware adds.
    middleware = KiotaClientFactory.get_default_middleware(options)
    for handler in middleware:
        if isinstance(handler, RetryHandler):
            handler.retry_on_status_codes = (
                handler.retry_on_status_codes | GRAPH_EXTRA_RETRY_STATUS_CODES
            )
    middleware.append(
        GraphTelemetryHandler(
            options=options[GraphTelemetryHandlerOption.get_key()],
        )
    )
    client = GraphClientFactory.create_with_custom_middleware(middleware)
    request_adapter = GraphRequestAdapter(
        AzureIdentityAuthenticationProvider(credentials, scopes=GRAPH_SCOPES),
        client=client,
    )
    return GraphServiceClient(request_adapter=request_adapter)


def get_api_error_response_header(
    error: APIError,
    header_name: str,
) -> str | None:
    response_headers = error.response_headers
    if not isinstance(response_headers, Mapping):
        return None

    target = header_name.lower()
    for key, value in response_headers.items():
        if str(key).lower() == target:
            return str(value)
    return None
