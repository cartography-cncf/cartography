from unittest.mock import Mock

import requests

from cartography.intel.gitlab import util
from cartography.intel.gitlab.util import fetch_registry_manifest
from cartography.intel.gitlab.util import get_paginated
from cartography.intel.gitlab.util import get_registry_token
from cartography.intel.gitlab.util import get_single


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
    monkeypatch.setattr("cartography.intel.gitlab.util._session.request", _request)
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
    monkeypatch.setattr("cartography.intel.gitlab.util._session.request", _request)
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
        "cartography.intel.gitlab.util._session.request",
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


def test_get_single_and_get_paginated_reuse_shared_session(monkeypatch):
    # Arrange: get_single and get_paginated are independent call paths (as are
    # runners.sync_gitlab_runners and supply_chain.get_dockerfiles_for_projects,
    # which route through get_paginated too). They must all dispatch through the
    # same requests.Session so the underlying connection pool - and therefore
    # any pooled/keep-alive TCP connections - is actually shared instead of each
    # call path opening its own.
    assert isinstance(util._session, requests.Session)

    seen_sessions = []
    single_response = _make_response(200, {"id": 1})
    paginated_response = _make_response(200, [{"id": 1}], headers={})

    def _request(method, url, **kwargs):
        seen_sessions.append(util._session)
        if url.endswith("/single"):
            return single_response
        return paginated_response

    monkeypatch.setattr("cartography.intel.gitlab.util._session.request", _request)

    # Act
    get_single("https://gitlab.example.com", "tok", "/single")
    get_paginated("https://gitlab.example.com", "tok", "/list")

    # Assert
    assert len(seen_sessions) == 2
    assert seen_sessions[0] is seen_sessions[1] is util._session


def test_fetch_registry_manifest_forwards_head_method(monkeypatch):
    # Arrange: a HEAD probe must reach the registry as HEAD, including on the
    # post-401 retry, so a digest can be resolved without a body transfer.
    methods = []
    responses = iter(
        [
            _make_response(401),
            _make_response(200, {}),
        ],
    )

    monkeypatch.setattr(
        "cartography.intel.gitlab.util.get_registry_token",
        lambda *args, **kwargs: "jwt-token",
    )

    def _request(method, *args, **kwargs):
        methods.append(method)
        return next(responses)

    monkeypatch.setattr(
        "cartography.intel.gitlab.util._session.request",
        _request,
    )

    # Act
    response = fetch_registry_manifest(
        "https://gitlab.example.com",
        "https://registry.example.com",
        "group/project",
        "latest",
        "pat",
        method="HEAD",
    )

    # Assert
    assert response.status_code == 200
    assert methods == ["HEAD", "HEAD"]
