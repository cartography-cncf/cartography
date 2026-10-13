from types import SimpleNamespace
from unittest.mock import patch

import pytest
from google.api_core.exceptions import GoogleAPICallError
from google.api_core.exceptions import MethodNotImplemented
from google.api_core.exceptions import PermissionDenied
from google.api_core.exceptions import ServiceUnavailable

from cartography.intel.gcp import vertex
from cartography.intel.gcp.util import GCP_API_MAX_RETRIES
from cartography.intel.gcp.vertex.utils import fetch_vertex_ai_resources_for_locations
from cartography.intel.gcp.vertex.utils import (
    filter_locations_to_supported_vertex_locations,
)
from cartography.intel.gcp.vertex.utils import list_vertex_ai_resources_for_location


@patch("time.sleep", return_value=None)
def test_list_vertex_ai_resources_for_location_retries_transient_gapic_errors(
    _mock_sleep,
    monkeypatch,
):
    monkeypatch.setattr(
        vertex.utils,
        "proto_message_to_dict",
        lambda resource: {"name": resource.name},
    )
    calls = 0

    def fetcher():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ServiceUnavailable("transient backend error")
        return [SimpleNamespace(name="model-1")]

    assert list_vertex_ai_resources_for_location(
        fetcher=fetcher,
        resource_type="models",
        location="us-central1",
        project_id="test-project",
    ) == [{"name": "model-1"}]
    assert calls == 2


@patch("time.sleep", return_value=None)
def test_list_vertex_ai_resources_for_location_raises_after_exhausting_transient_gapic_errors(
    _mock_sleep,
):
    calls = 0

    def fetcher():
        nonlocal calls
        calls += 1
        raise ServiceUnavailable("transient backend error")

    with pytest.raises(ServiceUnavailable):
        list_vertex_ai_resources_for_location(
            fetcher=fetcher,
            resource_type="models",
            location="us-central1",
            project_id="test-project",
        )
    assert calls == GCP_API_MAX_RETRIES


def test_list_vertex_ai_resources_for_location_permission_denied_returns_empty():
    calls = 0

    def fetcher():
        nonlocal calls
        calls += 1
        raise PermissionDenied("permission denied")

    assert (
        list_vertex_ai_resources_for_location(
            fetcher=fetcher,
            resource_type="models",
            location="us-central1",
            project_id="test-project",
        )
        == []
    )
    assert calls == 1


@patch("time.sleep", return_value=None)
def test_list_vertex_ai_resources_for_location_method_not_implemented_returns_empty(
    _mock_sleep,
):
    calls = 0

    def fetcher():
        nonlocal calls
        calls += 1
        raise MethodNotImplemented("501 Received http2 header with status: 404")

    assert (
        list_vertex_ai_resources_for_location(
            fetcher=fetcher,
            resource_type="models",
            location="us-central1",
            project_id="test-project",
        )
        == []
    )
    # Must not retry: MethodNotImplemented is a ServerError subclass but means
    # the regional endpoint is unavailable.
    assert calls == 1


def test_list_vertex_ai_resources_for_location_reraises_google_api_call_errors():
    with pytest.raises(GoogleAPICallError):
        list_vertex_ai_resources_for_location(
            fetcher=lambda: (_ for _ in ()).throw(GoogleAPICallError("boom")),
            resource_type="models",
            location="us-central1",
            project_id="test-project",
        )


def test_filter_locations_to_supported_vertex_locations_splits_supported_and_unsupported():
    supported, unsupported = filter_locations_to_supported_vertex_locations(
        ["us-central1", "not-a-real-location", "europe-west1", "us-central1"],
    )
    assert supported == ["us-central1", "europe-west1", "us-central1"]
    assert unsupported == ["not-a-real-location"]


def test_filter_locations_to_supported_vertex_locations_falls_back_when_metadata_empty():
    supported, unsupported = filter_locations_to_supported_vertex_locations(
        ["us-central1", "custom-location"],
        available_locations=frozenset(),
    )
    assert supported == ["us-central1", "custom-location"]
    assert unsupported == []


def test_fetch_vertex_ai_resources_for_locations_skips_unsupported_locations():
    fetched: list[str] = []

    def fetch_for_location(location: str) -> list[dict]:
        fetched.append(location)
        return [{"name": location}]

    resources = fetch_vertex_ai_resources_for_locations(
        locations=["us-central1", "not-a-real-location", "europe-west1"],
        project_id="test-project",
        resource_type="models",
        fetch_for_location=fetch_for_location,
        max_workers=1,
    )

    assert fetched == ["us-central1", "europe-west1"]
    assert resources == [{"name": "us-central1"}, {"name": "europe-west1"}]
