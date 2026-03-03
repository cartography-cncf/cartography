from unittest.mock import MagicMock

from cartography.intel.gcp.vertex.instances import get_workbench_api_locations
from cartography.intel.gcp.vertex.instances import get_workbench_instances_for_location


def test_get_workbench_api_locations_uses_authorized_session(monkeypatch):
    mock_aiplatform = MagicMock()
    mock_creds = MagicMock()
    mock_aiplatform._http.credentials = mock_creds

    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "locations": [
            {"locationId": "us-central1"},
            {"locationId": "us-central1-a"},
            {"locationId": "antarctica-south1"},
        ]
    }
    mock_session.get.return_value = mock_response

    monkeypatch.setattr(
        "google.auth.transport.requests.AuthorizedSession",
        lambda credentials: mock_session,
    )

    locations = get_workbench_api_locations(mock_aiplatform, "test-project")

    assert locations == ["us-central1", "us-central1-a"]
    mock_session.get.assert_called_once_with(
        "https://notebooks.googleapis.com/v1/projects/test-project/locations",
        timeout=60,
    )


def test_get_workbench_api_locations_handles_unauthorized(monkeypatch, caplog):
    mock_aiplatform = MagicMock()
    mock_aiplatform._http.credentials = MagicMock()

    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.reason = "Unauthorized"
    mock_session.get.return_value = mock_response

    monkeypatch.setattr(
        "google.auth.transport.requests.AuthorizedSession",
        lambda credentials: mock_session,
    )

    with caplog.at_level("WARNING"):
        locations = get_workbench_api_locations(mock_aiplatform, "test-project")

    assert locations == []
    assert any(
        "Unauthorized when trying to get Notebooks API locations for project test-project"
        in rec.message
        for rec in caplog.records
    )


def test_get_workbench_instances_for_location_uses_authorized_session(monkeypatch):
    mock_aiplatform = MagicMock()
    mock_aiplatform._http.credentials = MagicMock()

    mock_session = MagicMock()
    page_1 = MagicMock()
    page_1.status_code = 200
    page_1.json.return_value = {
        "instances": [{"name": "instance-1"}],
        "nextPageToken": "token-1",
    }
    page_2 = MagicMock()
    page_2.status_code = 200
    page_2.json.return_value = {"instances": [{"name": "instance-2"}]}
    mock_session.get.side_effect = [page_1, page_2]

    monkeypatch.setattr(
        "google.auth.transport.requests.AuthorizedSession",
        lambda credentials: mock_session,
    )

    instances = get_workbench_instances_for_location(
        mock_aiplatform,
        "test-project",
        "us-central1",
    )
    assert instances == [{"name": "instance-1"}, {"name": "instance-2"}]
    assert mock_session.get.call_count == 2
