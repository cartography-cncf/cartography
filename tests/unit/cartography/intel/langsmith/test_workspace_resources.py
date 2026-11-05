from unittest.mock import MagicMock

import pytest
import requests

from cartography.intel.langsmith.util import LangSmithFetchError
from cartography.intel.langsmith.workspace_resources import get_mcp_servers


def _http_error(status_code: int) -> requests.HTTPError:
    response = MagicMock()
    response.status_code = status_code
    return requests.HTTPError(f"{status_code} Client Error", response=response)


def _client(gateway_side_effect):
    client = MagicMock()
    client.get.return_value = {
        "mcp_vendors": [{"vendor_id": "arcade"}, {"vendor_id": "composio"}]
    }
    client.get_paginated_envelope.side_effect = gateway_side_effect
    return client


@pytest.mark.parametrize(
    "first_vendor_error, expected_complete",
    [
        # Registered but not OAuth-connected: it has no gateways, which is a full answer.
        (_http_error(400), True),
        # The vendor route is not served: also nothing to list.
        (LangSmithFetchError("/mcp-servers", 404, "HTTP 404"), True),
        # Hidden from this credential: gateways may exist, so cleanup must be skipped.
        (LangSmithFetchError("/mcp-servers", 403, "HTTP 403"), False),
    ],
)
def test_get_mcp_servers_skips_a_failing_vendor(first_vendor_error, expected_complete):
    # Arrange
    client = _client(
        [
            first_vendor_error,
            [{"id": "gw-1", "name": "Composio gateway", "tools": []}],
        ]
    )

    # Act
    servers, complete = get_mcp_servers(client, "org-1", "ws-1")

    # Assert
    assert [s["id"] for s in servers] == ["gw-1"]
    assert complete is expected_complete


def test_get_mcp_servers_reraises_other_http_errors():
    # Arrange
    client = _client([_http_error(500)])

    # Act and assert
    with pytest.raises(requests.HTTPError):
        get_mcp_servers(client, "org-1", "ws-1")
