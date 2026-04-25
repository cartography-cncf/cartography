from types import SimpleNamespace
from unittest.mock import patch

import pytest
from google.api_core.exceptions import GoogleAPICallError
from google.api_core.exceptions import PermissionDenied
from google.api_core.exceptions import ServiceUnavailable

from cartography.intel.gcp.artifact_registry.util import (
    fetch_artifact_registry_resources,
)
from cartography.intel.gcp.artifact_registry.util import get_artifact_registry_locations
from cartography.intel.gcp.artifact_registry.util import (
    list_artifact_registry_resources,
)
from cartography.intel.gcp.util import GCP_API_MAX_RETRIES


def test_get_artifact_registry_locations_success():
    client = SimpleNamespace(
        list_locations=lambda request: SimpleNamespace(
            locations=[
                SimpleNamespace(location_id="us-central1"),
                SimpleNamespace(location_id="europe-west1"),
            ]
        )
    )

    locations = get_artifact_registry_locations(client, "test-project")
    assert locations == ["us-central1", "europe-west1"]


def test_get_artifact_registry_locations_forbidden_returns_none(caplog):
    def _raise_permission_denied(request):
        raise PermissionDenied("permission denied")

    client = SimpleNamespace(list_locations=_raise_permission_denied)

    locations = get_artifact_registry_locations(client, "test-project")

    assert locations is None
    assert "Skipping Artifact Registry cleanup" in caplog.text


@patch("time.sleep", return_value=None)
def test_get_artifact_registry_locations_retries_transient_gapic_error(_):
    calls = 0

    def _list_locations(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ServiceUnavailable("transient backend error")
        return SimpleNamespace(locations=[SimpleNamespace(location_id="us-central1")])

    client = SimpleNamespace(list_locations=_list_locations)

    assert get_artifact_registry_locations(client, "test-project") == ["us-central1"]
    assert calls == 2


def test_list_artifact_registry_resources_does_not_retry_non_retryable_gapic_error():
    calls = 0

    def _fetcher():
        nonlocal calls
        calls += 1
        raise PermissionDenied("permission denied")

    with pytest.raises(PermissionDenied):
        list_artifact_registry_resources(_fetcher)

    assert calls == 1


@patch("time.sleep", return_value=None)
def test_list_artifact_registry_resources_raises_after_exhausting_retries(_):
    calls = 0

    def _fetcher():
        nonlocal calls
        calls += 1
        raise ServiceUnavailable("transient backend error")

    with pytest.raises(ServiceUnavailable):
        list_artifact_registry_resources(_fetcher)

    assert calls == GCP_API_MAX_RETRIES


def test_get_artifact_registry_locations_unknown_error_raises(caplog):
    def _raise_api_error(request):
        raise GoogleAPICallError("backend error")

    client = SimpleNamespace(list_locations=_raise_api_error)

    with pytest.raises(GoogleAPICallError):
        get_artifact_registry_locations(client, "test-project")


def test_fetch_artifact_registry_resources_preserves_input_order():
    result = fetch_artifact_registry_resources(
        items=[3, 1, 2],
        fetch_for_item=lambda item: item * 10,
        resource_type="test resources",
        project_id="test-project",
        max_workers=3,
    )

    assert result == [30, 10, 20]


def test_fetch_artifact_registry_resources_propagates_unexpected_errors():
    def _raise(item):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        fetch_artifact_registry_resources(
            items=[1],
            fetch_for_item=_raise,
            resource_type="test resources",
            project_id="test-project",
        )
