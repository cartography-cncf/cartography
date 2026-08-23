from types import SimpleNamespace
from unittest.mock import patch

import pytest
from google.api_core.exceptions import GoogleAPICallError
from google.api_core.exceptions import PermissionDenied
from google.api_core.exceptions import ServiceUnavailable

from cartography.intel.gcp import vertex
from cartography.intel.gcp.util import GCP_API_MAX_RETRIES
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


def test_list_vertex_ai_resources_for_location_reraises_google_api_call_errors():
    with pytest.raises(GoogleAPICallError):
        list_vertex_ai_resources_for_location(
            fetcher=lambda: (_ for _ in ()).throw(GoogleAPICallError("boom")),
            resource_type="models",
            location="us-central1",
            project_id="test-project",
        )


@pytest.mark.parametrize("use_session", [True, False])
def test_paginate_vertex_api_uses_timeout(use_session, monkeypatch):
    calls = []

    def mock_get(url, headers=None, params=None, timeout=None):
        calls.append((url, headers, params, timeout))
        mock_resp = SimpleNamespace()
        mock_resp.status_code = 200
        if len(calls) == 1:
            mock_resp.json = lambda: {"instances": [{"name": "inst-1"}], "nextPageToken": "token2"}
        else:
            mock_resp.json = lambda: {"instances": [{"name": "inst-2"}]}
        return mock_resp

    from cartography.intel.gcp.vertex import utils
    from cartography.intel.gcp.vertex.utils import _TIMEOUT
    from cartography.intel.gcp.vertex.utils import paginate_vertex_api

    if use_session:
        session = SimpleNamespace(get=mock_get)
    else:
        session = None
        monkeypatch.setattr(utils.requests, "get", mock_get)

    res = paginate_vertex_api(
        url="https://example.com/api",
        headers={"Auth": "token"},
        resource_type="instances",
        response_key="instances",
        location="us-central1",
        project_id="test-proj",
        session=session,
    )

    assert res == [{"name": "inst-1"}, {"name": "inst-2"}]
    assert len(calls) == 2
    assert calls[0][3] == _TIMEOUT
    assert calls[1][3] == _TIMEOUT


