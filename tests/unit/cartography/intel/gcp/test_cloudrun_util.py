from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from google.api_core.exceptions import DeadlineExceeded
from google.api_core.exceptions import GoogleAPICallError
from google.api_core.exceptions import PermissionDenied
from googleapiclient.errors import HttpError

from cartography.intel.gcp.cloudrun.util import build_cloud_run_resource_retry
from cartography.intel.gcp.cloudrun.util import CLOUD_RUN_LIST_TIMEOUT
from cartography.intel.gcp.cloudrun.util import discover_cloud_run_locations
from cartography.intel.gcp.cloudrun.util import fetch_cloud_run_resources_for_locations
from cartography.intel.gcp.cloudrun.util import list_cloud_run_resources_for_location


def _http_error(status: int) -> HttpError:
    resp = MagicMock()
    resp.status = status
    return HttpError(resp=resp, content=b"{}")


def test_discover_cloud_run_locations_prefers_provided_credentials_and_sorts():
    mock_v1_client = MagicMock()
    mock_request = MagicMock()
    mock_request.execute.return_value = {
        "locations": [
            {"name": "projects/test-project/locations/us-west1"},
            {"name": "test-project/locations/us-central1"},
            {"name": "projects/test-project/locations/us-west1"},
        ],
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

    assert result == [
        "projects/test-project/locations/us-central1",
        "projects/test-project/locations/us-west1",
    ]
    mock_build_client.assert_called_once_with(
        "run",
        "v1",
        credentials=mock_credentials,
    )
    mock_get_gcp_credentials.assert_not_called()


def test_discover_cloud_run_locations_returns_none_on_api_disabled():
    mock_v1_client = MagicMock()
    mock_request = MagicMock()
    mock_request.execute.side_effect = _http_error(403)
    mock_v1_client.projects.return_value.locations.return_value.list.return_value = (
        mock_request
    )

    with (
        patch(
            "cartography.intel.gcp.cloudrun.util.build_client",
            return_value=mock_v1_client,
        ),
        patch(
            "cartography.intel.gcp.cloudrun.util.is_api_disabled_error",
            return_value=True,
        ),
    ):
        result = discover_cloud_run_locations(
            client=MagicMock(),
            project_id="test-project",
            credentials=MagicMock(),
        )

    assert result is None


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

    assert result == [
        "projects/test-project/locations/europe-west1",
        "projects/test-project/locations/us-west1",
    ]


def test_discover_cloud_run_locations_falls_back_when_v1_returns_no_locations():
    mock_client = MagicMock()
    mock_v1_client = MagicMock()
    empty_locations_request = MagicMock()
    empty_locations_request.execute.return_value = {"locations": []}
    mock_v1_client.projects.return_value.locations.return_value.list.return_value = (
        empty_locations_request
    )
    mock_v1_client.projects.return_value.locations.return_value.list_next.return_value = (
        None
    )

    mock_services_request = MagicMock()
    mock_services_request.execute.return_value = {
        "services": [
            {"name": "projects/test-project/locations/us-west1/services/svc-1"},
        ],
    }
    services = (
        mock_client.projects.return_value.locations.return_value.services.return_value
    )
    services.list.return_value = mock_services_request
    services.list_next.return_value = None

    with patch(
        "cartography.intel.gcp.cloudrun.util.build_client",
        return_value=mock_v1_client,
    ):
        result = discover_cloud_run_locations(
            client=mock_client,
            project_id="test-project",
            credentials=MagicMock(),
        )

    assert result == ["projects/test-project/locations/us-west1"]


def test_list_cloud_run_resources_for_location_skips_permission_denied():
    def _fetcher(**_):
        raise PermissionDenied("nope")

    result = list_cloud_run_resources_for_location(
        fetcher=_fetcher,
        resource_type="jobs",
        location="projects/test-project/locations/us-central1",
        project_id="test-project",
    )

    assert result == []


def test_list_cloud_run_resources_for_location_reraises_google_api_call_error():
    def _fetcher(**_):
        raise GoogleAPICallError("boom")

    with pytest.raises(GoogleAPICallError):
        list_cloud_run_resources_for_location(
            fetcher=_fetcher,
            resource_type="jobs",
            location="projects/test-project/locations/us-central1",
            project_id="test-project",
        )


def test_list_cloud_run_resources_for_location_passes_retry_and_timeout(mocker):
    mock_retry = MagicMock()
    mock_build_retry = mocker.patch(
        "cartography.intel.gcp.cloudrun.util.build_cloud_run_resource_retry",
        return_value=mock_retry,
    )
    mocker.patch(
        "cartography.intel.gcp.cloudrun.util.proto_message_to_dict",
        side_effect=lambda resource: resource,
    )
    received_kwargs = {}

    def _fetcher(**kwargs):
        received_kwargs.update(kwargs)
        return [{"id": "service-1"}]

    result = list_cloud_run_resources_for_location(
        fetcher=_fetcher,
        resource_type="services",
        location="projects/test-project/locations/us-central1",
        project_id="test-project",
    )

    assert result == [{"id": "service-1"}]
    assert received_kwargs == {
        "retry": mock_retry,
        "timeout": CLOUD_RUN_LIST_TIMEOUT,
    }
    mock_build_retry.assert_called_once_with(
        resource_type="services",
        location="projects/test-project/locations/us-central1",
        project_id="test-project",
    )


def test_build_cloud_run_resource_retry_retries_deadline_exceeded(mocker):
    mocker.patch("time.sleep")
    retry = build_cloud_run_resource_retry(
        resource_type="services",
        location="projects/test-project/locations/us-central1",
        project_id="test-project",
    )

    calls = 0

    def fetch_resource():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise DeadlineExceeded("slow")
        return [{"id": "service-1"}]

    result = retry(fetch_resource)()

    assert result == [{"id": "service-1"}]
    assert calls == 2


def test_list_cloud_run_resources_for_location_uses_retry_for_deadline_exceeded(
    mocker,
):
    mocker.patch("time.sleep")
    mocker.patch(
        "cartography.intel.gcp.cloudrun.util.proto_message_to_dict",
        side_effect=lambda resource: resource,
    )
    calls = 0

    def _fetcher(*, retry, timeout):
        assert timeout == CLOUD_RUN_LIST_TIMEOUT

        def _list_resources():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise DeadlineExceeded("slow")
            return [{"id": "service-1"}]

        return retry(_list_resources)()

    result = list_cloud_run_resources_for_location(
        fetcher=_fetcher,
        resource_type="services",
        location="projects/test-project/locations/us-central1",
        project_id="test-project",
    )

    assert result == [{"id": "service-1"}]
    assert calls == 2


def test_fetch_cloud_run_resources_for_locations_dedupes_and_preserves_input_order():
    visited_locations: list[str] = []

    def fetch_for_location(location: str) -> list[dict]:
        visited_locations.append(location)
        return [{"id": location}]

    result = fetch_cloud_run_resources_for_locations(
        locations=[
            "projects/test-project/locations/us-west1",
            "projects/test-project/locations/us-central1",
            "projects/test-project/locations/us-west1",
        ],
        project_id="test-project",
        resource_type="services",
        fetch_for_location=fetch_for_location,
        max_workers=3,
    )

    assert visited_locations.count("projects/test-project/locations/us-west1") == 1
    assert visited_locations.count("projects/test-project/locations/us-central1") == 1
    assert result == [
        {"id": "projects/test-project/locations/us-west1"},
        {"id": "projects/test-project/locations/us-central1"},
    ]
