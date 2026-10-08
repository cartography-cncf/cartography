import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from googleapiclient.errors import HttpError

from cartography.intel.gcp.gke import get_gke_clusters


def _make_http_error(status: int) -> HttpError:
    mock_resp = MagicMock()
    mock_resp.status = status
    return HttpError(mock_resp, json.dumps({"error": {"code": status}}).encode())


class TestGetGkeClustersPartialScanSafety:
    """Permission failures are unknown inventory, not authoritative emptiness."""

    def test_preserves_unknown_on_forbidden(self):
        mock_container = MagicMock()
        with (
            patch(
                "cartography.intel.gcp.gke.gcp_api_execute_with_retry",
                side_effect=_make_http_error(403),
            ),
            patch(
                "cartography.intel.gcp.gke.classify_gcp_http_error",
                return_value="forbidden",
            ),
        ):
            assert get_gke_clusters(mock_container, "test-project") is None

    def test_preserves_unknown_on_api_disabled(self):
        mock_container = MagicMock()
        with (
            patch(
                "cartography.intel.gcp.gke.gcp_api_execute_with_retry",
                side_effect=_make_http_error(403),
            ),
            patch(
                "cartography.intel.gcp.gke.classify_gcp_http_error",
                return_value="api_disabled",
            ),
        ):
            assert get_gke_clusters(mock_container, "test-project") is None

    def test_preserves_unknown_on_billing_disabled(self):
        mock_container = MagicMock()
        with (
            patch(
                "cartography.intel.gcp.gke.gcp_api_execute_with_retry",
                side_effect=_make_http_error(403),
            ),
            patch(
                "cartography.intel.gcp.gke.classify_gcp_http_error",
                return_value="billing_disabled",
            ),
        ):
            assert get_gke_clusters(mock_container, "test-project") is None

    def test_reraises_on_unexpected_error(self):
        mock_container = MagicMock()
        with (
            patch(
                "cartography.intel.gcp.gke.gcp_api_execute_with_retry",
                side_effect=_make_http_error(500),
            ),
            patch(
                "cartography.intel.gcp.gke.classify_gcp_http_error",
                return_value="transient",
            ),
        ):
            with pytest.raises(HttpError):
                get_gke_clusters(mock_container, "test-project")
