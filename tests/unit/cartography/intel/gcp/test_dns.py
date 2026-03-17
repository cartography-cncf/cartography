import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from googleapiclient.errors import HttpError

from cartography.intel.gcp.dns import get_dns_rrs
from cartography.intel.gcp.dns import get_dns_zones


def _make_http_error(status: int) -> HttpError:
    mock_resp = MagicMock()
    mock_resp.status = status
    return HttpError(mock_resp, json.dumps({"error": {"code": status}}).encode())


class TestGetDnsZonesCurrentStateSemantics:
    """
    Verify current-state semantics for get_dns_zones.

    On permission or API-disabled errors, returning [] (instead of raising) lets
    the cleanup step remove any previously ingested zones from the graph, ensuring
    the graph reflects only the currently visible state.
    """

    def test_returns_empty_list_on_forbidden(self):
        mock_dns = MagicMock()
        with (
            patch(
                "cartography.intel.gcp.dns.gcp_api_execute_with_retry",
                side_effect=_make_http_error(403),
            ),
            patch(
                "cartography.intel.gcp.dns.classify_gcp_http_error",
                return_value="forbidden",
            ),
        ):
            assert get_dns_zones(mock_dns, "test-project") == []

    def test_returns_empty_list_on_api_disabled(self):
        mock_dns = MagicMock()
        with (
            patch(
                "cartography.intel.gcp.dns.gcp_api_execute_with_retry",
                side_effect=_make_http_error(403),
            ),
            patch(
                "cartography.intel.gcp.dns.classify_gcp_http_error",
                return_value="api_disabled",
            ),
        ):
            assert get_dns_zones(mock_dns, "test-project") == []

    def test_reraises_on_unexpected_error(self):
        mock_dns = MagicMock()
        with (
            patch(
                "cartography.intel.gcp.dns.gcp_api_execute_with_retry",
                side_effect=_make_http_error(500),
            ),
            patch(
                "cartography.intel.gcp.dns.classify_gcp_http_error",
                return_value="transient",
            ),
        ):
            with pytest.raises(HttpError):
                get_dns_zones(mock_dns, "test-project")


class TestGetDnsRrsCurrentStateSemantics:
    """
    Verify current-state semantics for get_dns_rrs.

    Same rationale as get_dns_zones: returning [] on access errors allows
    the cleanup step to remove stale record sets from the graph.
    """

    def test_returns_empty_list_on_forbidden(self):
        mock_dns = MagicMock()
        zones = [{"id": "zone-1"}]
        with (
            patch(
                "cartography.intel.gcp.dns.gcp_api_execute_with_retry",
                side_effect=_make_http_error(403),
            ),
            patch(
                "cartography.intel.gcp.dns.classify_gcp_http_error",
                return_value="forbidden",
            ),
        ):
            assert get_dns_rrs(mock_dns, zones, "test-project") == []

    def test_returns_empty_list_on_api_disabled(self):
        mock_dns = MagicMock()
        zones = [{"id": "zone-1"}]
        with (
            patch(
                "cartography.intel.gcp.dns.gcp_api_execute_with_retry",
                side_effect=_make_http_error(403),
            ),
            patch(
                "cartography.intel.gcp.dns.classify_gcp_http_error",
                return_value="api_disabled",
            ),
        ):
            assert get_dns_rrs(mock_dns, zones, "test-project") == []
