from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.gcp.cloudrun.util import discover_cloud_run_locations


def test_discover_cloud_run_locations_prefers_provided_credentials():
    mock_v1_client = MagicMock()
    mock_request = MagicMock()
    mock_request.execute.return_value = {
        "locations": [{"name": "projects/test-project/locations/us-central1"}],
    }
    mock_v1_client.projects.return_value.locations.return_value.list.return_value = (
        mock_request
    )
    mock_v1_client.projects.return_value.locations.return_value.list_next.return_value = (
        None
    )

    mock_credentials = MagicMock()
    with (
        patch(
            "cartography.intel.gcp.cloudrun.util.build_client",
            return_value=mock_v1_client,
        ) as mock_build_client,
        patch(
            "cartography.intel.gcp.cloudrun.util.get_gcp_credentials",
        ) as mock_get_gcp_credentials,
    ):
        result = discover_cloud_run_locations(
            client=MagicMock(),
            project_id="test-project",
            credentials=mock_credentials,
        )

    assert result == {"projects/test-project/locations/us-central1"}
    mock_build_client.assert_called_once_with(
        "run",
        "v1",
        credentials=mock_credentials,
    )
    mock_get_gcp_credentials.assert_not_called()


def test_discover_cloud_run_locations_falls_back_when_v1_discovery_unavailable():
    mock_client = MagicMock()

    mock_services_request = MagicMock()
    mock_services_request.execute.return_value = {
        "services": [
            {"name": "projects/test-project/locations/us-west1/services/svc-1"},
            {"name": "projects/test-project/locations/europe-west1/services/svc-2"},
        ],
    }

    services = (
        mock_client.projects.return_value.locations.return_value.services.return_value
    )
    services.list.return_value = mock_services_request
    services.list_next.return_value = None

    with patch(
        "cartography.intel.gcp.cloudrun.util.build_client",
        side_effect=RuntimeError(
            "GCP credentials are not available; cannot build client."
        ),
    ):
        result = discover_cloud_run_locations(
            client=mock_client,
            project_id="test-project",
        )

    assert result == {
        "projects/test-project/locations/europe-west1",
        "projects/test-project/locations/us-west1",
    }
