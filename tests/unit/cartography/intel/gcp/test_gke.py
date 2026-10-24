import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from googleapiclient.errors import HttpError

from cartography.intel.gcp.gke import get_gke_clusters
from cartography.intel.gcp.gke import sync_gke_clusters


def _make_http_error(status: int) -> HttpError:
    mock_resp = MagicMock()
    mock_resp.status = status
    return HttpError(mock_resp, json.dumps({"error": {"code": status}}).encode())


class TestGetGkeClustersCurrentStateSemantics:
    """
    Verify current-state semantics for get_gke_clusters.

    On permission or API-disabled errors, returning {} (instead of raising) lets
    the cleanup step remove any previously ingested clusters from the graph, ensuring
    the graph reflects only the currently visible state.
    """

    def test_returns_empty_dict_on_forbidden(self):
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
            assert get_gke_clusters(mock_container, "test-project") == {}

    def test_returns_empty_dict_on_api_disabled(self):
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
            assert get_gke_clusters(mock_container, "test-project") == {}

    def test_returns_empty_dict_on_billing_disabled(self):
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
            assert get_gke_clusters(mock_container, "test-project") == {}

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


@patch("cartography.intel.gcp.gke.cleanup_gke_clusters")
@patch("cartography.intel.gcp.gke.sync_labels")
@patch("cartography.intel.gcp.gke.load")
def test_sync_skips_labels_and_cleanup_when_zones_are_missing(
    mock_load, mock_sync_labels, mock_cleanup
):
    # Arrange
    container = MagicMock()
    container.projects.return_value.zones.return_value.clusters.return_value.list.return_value.execute.return_value = {
        "clusters": [
            {
                "name": "example",
                "selfLink": "https://container.googleapis.com/v1/projects/test-project/locations/us-central1/clusters/example",
            },
        ],
        "missingZones": ["us-east1-b"],
    }

    # Act
    sync_gke_clusters(
        MagicMock(),
        container,
        "test-project",
        1,
        {"UPDATE_TAG": 1, "PROJECT_ID": "test-project"},
    )

    # Assert
    mock_load.assert_called_once()
    mock_sync_labels.assert_not_called()
    mock_cleanup.assert_not_called()
