from types import SimpleNamespace

import pytest
from google.api_core.exceptions import GoogleAPICallError
from google.api_core.exceptions import PermissionDenied

from cartography.intel.gcp.artifact_registry.util import (
    fetch_artifact_registry_resources,
)
from cartography.intel.gcp.artifact_registry.util import get_artifact_registry_locations


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


def test_get_artifact_registry_locations_unknown_error_returns_none(caplog):
    def _raise_api_error(request):
        raise GoogleAPICallError("backend error")

    client = SimpleNamespace(list_locations=_raise_api_error)

    locations = get_artifact_registry_locations(client, "test-project")

    assert locations is None
    assert "Failed to get Artifact Registry locations" in caplog.text


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
