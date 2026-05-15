from unittest.mock import Mock

import requests

from cartography.intel.gitlab import util
from cartography.intel.gitlab.util import fetch_registry_manifest
from cartography.intel.gitlab.util import get_registry_token


def _make_response(status_code: int, json_data=None, headers=None):
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    response.headers = headers or {}
    response.json.return_value = json_data or {}
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            f"{status_code} error",
            response=response,
        )
    else:
        response.raise_for_status.return_value = None
    return response


def test_get_registry_token_retries_transient_server_error(monkeypatch):
    calls = []
    responses = iter(
        [
            _make_response(502),
            _make_response(200, {"token": "jwt-token", "expires_in": 300}),
        ],
    )

    def _request(*args, **kwargs):
        calls.append((args, kwargs))
        return next(responses)

    util._registry_token_cache.clear()
    monkeypatch.setattr("cartography.intel.gitlab.util.requests.request", _request)
    monkeypatch.setattr("cartography.intel.gitlab.util.time.sleep", lambda _: None)

    token = get_registry_token(
        "https://gitlab.example.com",
        "https://registry.example.com",
        "group/project",
        "pat",
    )

    assert token == "jwt-token"
    assert len(calls) == 2


def test_fetch_registry_manifest_retries_connection_error(monkeypatch):
    attempts = 0
    success = _make_response(200, {"schemaVersion": 2})

    def _request(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise requests.exceptions.ConnectionError("connection reset")
        return success

    monkeypatch.setattr(
        "cartography.intel.gitlab.util.get_registry_token",
        lambda *args, **kwargs: "jwt-token",
    )
    monkeypatch.setattr("cartography.intel.gitlab.util.requests.request", _request)
    monkeypatch.setattr("cartography.intel.gitlab.util.time.sleep", lambda _: None)

    response = fetch_registry_manifest(
        "https://gitlab.example.com",
        "https://registry.example.com",
        "group/project",
        "latest",
        "pat",
    )

    assert response is success
    assert attempts == 2


def test_fetch_registry_manifest_refreshes_token_after_401(monkeypatch):
    token_calls = []
    responses = iter(
        [
            _make_response(401),
            _make_response(200, {"schemaVersion": 2}),
        ],
    )

    def _get_registry_token(*args, **kwargs):
        token_calls.append(kwargs.get("force_refresh", False))
        return "refreshed-token" if kwargs.get("force_refresh") else "jwt-token"

    monkeypatch.setattr(
        "cartography.intel.gitlab.util.get_registry_token",
        _get_registry_token,
    )
    monkeypatch.setattr(
        "cartography.intel.gitlab.util.requests.request",
        lambda *args, **kwargs: next(responses),
    )

    response = fetch_registry_manifest(
        "https://gitlab.example.com",
        "https://registry.example.com",
        "group/project",
        "latest",
        "pat",
    )

    assert response.status_code == 200
    assert token_calls == [False, True]
