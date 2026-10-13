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
    # which route through get_paginated too). None of them should construct a
    # new requests.Session - they should all reuse the shared module-level
    # _session so the underlying connection pool is actually shared.
    #
    # Track requests.Session.__init__ calls rather than asserting on `self`
    # identity from a patched request() - a prior test in this file patches
    # the *instance* attribute _session.request, and pytest's monkeypatch
    # restores that on teardown by re-setting it as a permanent instance
    # attribute (since it resolved via class inheritance), which would
    # silently shadow any later class-level patch of Session.request and
    # make an identity-based assertion unable to observe the real call.
    # Asserting no new Session gets constructed is what actually falls out
    # of a regression (a future change constructing a fresh Session per call).
    session_init_calls = []
    original_init = requests.Session.__init__

    def _tracking_init(self, *args, **kwargs):
        session_init_calls.append(self)
        return original_init(self, *args, **kwargs)

    monkeypatch.setattr(requests.Session, "__init__", _tracking_init)

    call_count = 0
    single_response = _make_response(200, {"id": 1})
    paginated_response = _make_response(200, [{"id": 1}], headers={})

    def _request(method, url, **kwargs):
        nonlocal call_count
        call_count += 1
        if url.endswith("/single"):
            return single_response
        return paginated_response

    monkeypatch.setattr(util._session, "request", _request)

    # Act
    get_single("https://gitlab.example.com", "tok", "/single")
    get_paginated("https://gitlab.example.com", "tok", "/list")

    # Assert
    assert call_count == 2
    assert session_init_calls == []


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
