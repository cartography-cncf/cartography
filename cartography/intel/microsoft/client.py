from collections.abc import Mapping
from typing import Any

from kiota_abstractions.api_error import APIError
from kiota_authentication_azure.azure_identity_authentication_provider import (
    AzureIdentityAuthenticationProvider,
)
from kiota_http.middleware.options.retry_handler_option import RetryHandlerOption
from msgraph import GraphServiceClient
from msgraph.graph_request_adapter import GraphRequestAdapter
from msgraph.graph_request_adapter import options as graph_request_adapter_options
from msgraph_core import GraphClientFactory

GRAPH_SCOPES = ["https://graph.microsoft.com/.default"]
GRAPH_RETRY_DELAY_SECONDS = 5.0
GRAPH_MAX_RETRIES = 6


def create_graph_service_client(credentials: Any) -> GraphServiceClient:
    retry_option = RetryHandlerOption(
        delay=GRAPH_RETRY_DELAY_SECONDS,
        max_retries=GRAPH_MAX_RETRIES,
    )
    client = GraphClientFactory.create_with_default_middleware(
        options={
            **graph_request_adapter_options,
            RetryHandlerOption.get_key(): retry_option,
        },
    )
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
