from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.gcp.cloudrun.util import discover_cloud_run_locations


def test_discover_cloud_run_locations_uses_authorized_session():
    mock_session = MagicMock()
    mock_response_page_1 = MagicMock()
    mock_response_page_1.status_code = 200
    mock_response_page_1.json.return_value = {
        "locations": [{"name": "projects/test-project/locations/us-central1"}],
        "nextPageToken": "next-page",
    }
    mock_response_page_2 = MagicMock()
    mock_response_page_2.status_code = 200
    mock_response_page_2.json.return_value = {
        "locations": [{"name": "test-project/locations/europe-west1"}],
    }
    mock_session.get.side_effect = [mock_response_page_1, mock_response_page_2]

    mock_credentials = MagicMock()
    with patch(
        "cartography.intel.gcp.cloudrun.util.build_authorized_session",
        return_value=mock_session,
    ) as mock_build_session:
        result = discover_cloud_run_locations(
            project_id="test-project",
            credentials=mock_credentials,
        )

    assert result == {
        "projects/test-project/locations/europe-west1",
        "projects/test-project/locations/us-central1",
    }
    mock_build_session.assert_called_once_with(credentials=mock_credentials)
    assert mock_session.get.call_count == 2


def test_discover_cloud_run_locations_returns_none_on_permission_denied():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_session.get.return_value = mock_response

    with patch(
        "cartography.intel.gcp.cloudrun.util.build_authorized_session",
        return_value=mock_session,
    ):
        result = discover_cloud_run_locations(project_id="test-project")

    assert result is None
