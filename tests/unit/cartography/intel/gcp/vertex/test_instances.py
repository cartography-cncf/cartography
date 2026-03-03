from unittest.mock import MagicMock
from unittest.mock import patch

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


def test_get_workbench_instances_for_location_passes_authorized_session(monkeypatch):
    mock_aiplatform = MagicMock()
    mock_aiplatform._http.credentials = MagicMock()

    mock_session = MagicMock()
    monkeypatch.setattr(
        "google.auth.transport.requests.AuthorizedSession",
        lambda credentials: mock_session,
    )

    with patch(
        "cartography.intel.gcp.vertex.utils.paginate_vertex_api",
        return_value=[],
    ) as mock_paginate:
        get_workbench_instances_for_location(
            mock_aiplatform,
            "test-project",
            "us-central1",
        )

    mock_paginate.assert_called_once_with(
        url="https://notebooks.googleapis.com/v2/projects/test-project/locations/us-central1/instances",
        headers={"Content-Type": "application/json"},
        resource_type="workbench instances",
        response_key="instances",
        location="us-central1",
        project_id="test-project",
        session=mock_session,
    )
