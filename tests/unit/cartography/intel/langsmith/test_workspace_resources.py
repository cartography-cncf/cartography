from collections import Counter
from unittest.mock import MagicMock

import pytest
import requests

from cartography.intel.langsmith import exposure
from cartography.intel.langsmith.util import LangSmithFetchError
from cartography.intel.langsmith.workspace_resources import get_mcp_servers
from tests.data.langsmith.fake_client import FakeLangSmithClient
from tests.data.langsmith.fake_client import SIMPSON_CORP_ROUTES
from tests.data.langsmith.workspaces import WORKSPACE_PROD_ID


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
    "first_vendor_error, expected_complete, expected_unconnected",
    [
        # Registered but not OAuth-connected: it has no gateways, which is a full answer.
        (_http_error(400), True, {"arcade": 1}),
        # The vendor route is not served: also nothing to list.
        (LangSmithFetchError("/mcp-servers", 404, "HTTP 404"), True, {}),
        # Hidden from this credential: gateways may exist, so cleanup must be skipped.
        (LangSmithFetchError("/mcp-servers", 403, "HTTP 403"), False, {}),
    ],
)
def test_get_mcp_servers_skips_a_failing_vendor(
    first_vendor_error, expected_complete, expected_unconnected
):
    # Arrange
    client = _client(
        [
            first_vendor_error,
            [{"id": "gw-1", "name": "Composio gateway", "tools": []}],
        ]
    )

    unconnected: Counter[str] = Counter()

    # Act
    servers, complete = get_mcp_servers(
        client, "org-1", "ws-1", unconnected_vendors=unconnected
    )

    # Assert
    assert [s["id"] for s in servers] == ["gw-1"]
    assert complete is expected_complete
    assert unconnected == expected_unconnected


def test_get_mcp_servers_reraises_other_http_errors():
    # Arrange
    client = _client([_http_error(500)])

    # Act and assert
    with pytest.raises(requests.HTTPError):
        get_mcp_servers(client, "org-1", "ws-1")


@pytest.mark.parametrize(
    "fetch, answering_route, sibling_route",
    [
        (
            exposure.get_public_shares,
            "/api/v1/workspaces/current/shared",
            "/api/v1/repos",
        ),
        (exposure.get_webhooks, "/api/v1/runs/rules", "/api/v1/prompt-webhooks"),
    ],
    ids=["shares", "webhooks"],
)
@pytest.mark.parametrize(
    "sibling_status, expected_complete",
    [(404, True), (403, False)],
    ids=["sibling not served", "sibling denied"],
)
def test_a_failed_sibling_listing_keeps_what_the_other_returned(
    fetch, answering_route, sibling_route, sibling_status, expected_complete
):
    # Arrange
    client = FakeLangSmithClient(failures={(sibling_route, "w1"): sibling_status})
    client.routes = {
        (answering_route, "w1"): SIMPSON_CORP_ROUTES[
            (answering_route, WORKSPACE_PROD_ID)
        ]
    }

    # Act
    rows, complete = fetch(client, "org-1", "w1")

    # Assert
    assert rows
    assert complete is expected_complete
