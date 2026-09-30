from unittest.mock import MagicMock

import pytest
import requests

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


def test_get_mcp_servers_skips_unconnected_vendor():
    # Arrange: the first vendor is not OAuth-connected and answers 400; the second lists.
    client = _client(
        [
            _http_error(400),
            [{"id": "gw-1", "name": "Composio gateway", "tools": []}],
        ]
    )

    # Act
    servers = get_mcp_servers(client, "org-1", "ws-1")

    # Assert: the unconnected vendor is skipped and the other vendor is still collected.
    assert [s["id"] for s in servers] == ["gw-1"]
    assert client.get_paginated_envelope.call_count == 2


def test_get_mcp_servers_reraises_other_http_errors():
    client = _client([_http_error(500)])

    with pytest.raises(requests.HTTPError):
        get_mcp_servers(client, "org-1", "ws-1")
