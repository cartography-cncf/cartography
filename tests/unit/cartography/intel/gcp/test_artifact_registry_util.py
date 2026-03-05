import json
from unittest.mock import MagicMock

import pytest
from googleapiclient.errors import HttpError

from cartography.intel.gcp.artifact_registry.util import get_artifact_registry_locations


def _make_http_error(status: int, payload: dict) -> HttpError:
    resp = MagicMock()
    resp.status = status
    return HttpError(resp=resp, content=json.dumps(payload).encode("utf-8"))


def _make_client() -> tuple[MagicMock, MagicMock]:
    client = MagicMock()
    request = MagicMock()
    client.projects.return_value.locations.return_value.list.return_value = request
    return client, request


def test_get_artifact_registry_locations_success(monkeypatch):
    client, _request = _make_client()
    monkeypatch.setattr(
        "cartography.intel.gcp.artifact_registry.util.gcp_api_execute_with_retry",
        lambda _req: {
            "locations": [{"locationId": "us-central1"}, {"locationId": "europe-west1"}]
        },
    )

    locations = get_artifact_registry_locations(client, "test-project")
    assert locations == ["us-central1", "europe-west1"]


def test_get_artifact_registry_locations_billing_disabled_returns_empty(monkeypatch):
    client, _request = _make_client()
    billing_error = _make_http_error(
        403,
        {
            "error": {
                "message": "This API method requires billing to be enabled.",
                "details": [
                    {
                        "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                        "reason": "BILLING_DISABLED",
                    }
                ],
            }
        },
    )
    monkeypatch.setattr(
        "cartography.intel.gcp.artifact_registry.util.gcp_api_execute_with_retry",
        lambda _req: (_ for _ in ()).throw(billing_error),
    )

    locations = get_artifact_registry_locations(client, "test-project")
    assert locations == []


def test_get_artifact_registry_locations_forbidden_returns_empty(monkeypatch):
    client, _request = _make_client()
    forbidden_error = _make_http_error(
        403,
        {
            "error": {
                "message": "Permission denied",
                "errors": [{"reason": "forbidden"}],
            }
        },
    )
    monkeypatch.setattr(
        "cartography.intel.gcp.artifact_registry.util.gcp_api_execute_with_retry",
        lambda _req: (_ for _ in ()).throw(forbidden_error),
    )

    locations = get_artifact_registry_locations(client, "test-project")
    assert locations == []


def test_get_artifact_registry_locations_unknown_error_raises(monkeypatch):
    client, _request = _make_client()
    server_error = _make_http_error(
        500,
        {
            "error": {
                "message": "internal error",
                "errors": [{"reason": "backendError"}],
            }
        },
    )
    monkeypatch.setattr(
        "cartography.intel.gcp.artifact_registry.util.gcp_api_execute_with_retry",
        lambda _req: (_ for _ in ()).throw(server_error),
    )

    with pytest.raises(HttpError):
        get_artifact_registry_locations(client, "test-project")
