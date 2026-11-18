from unittest.mock import Mock

import pytest
import requests

from cartography.intel.bitbucket.auth import BearerTokenCredential
from cartography.intel.bitbucket.auth import make_credential
from cartography.intel.bitbucket.auth import OAuth2RefreshCredential


def _make_response(json_data):
    response = Mock(spec=requests.Response)
    response.raise_for_status.return_value = None
    response.json.return_value = json_data
    return response


def test_make_credential_token():
    credential = make_credential("token", "my-token", None, None, None)
    assert isinstance(credential, BearerTokenCredential)
    assert credential.get_token() == "my-token"


def test_make_credential_token_missing_raises():
    with pytest.raises(ValueError):
        make_credential("token", None, None, None, None)


def test_make_credential_oauth():
    credential = make_credential(
        "oauth", None, "client-id", "client-secret", "refresh-token"
    )
    assert isinstance(credential, OAuth2RefreshCredential)


def test_make_credential_oauth_missing_raises():
    with pytest.raises(ValueError):
        make_credential("oauth", None, "client-id", None, "refresh-token")


def test_oauth_credential_fetches_and_caches_token(monkeypatch):
    calls = []

    def _post(url, data=None, auth=None, timeout=None):
        calls.append((url, data, auth))
        return _make_response({"access_token": "token-1", "expires_in": 7200})

    monkeypatch.setattr("cartography.intel.bitbucket.auth.requests.post", _post)

    credential = OAuth2RefreshCredential("client-id", "client-secret", "refresh-token")
    assert credential.get_token() == "token-1"
    # A second call before expiry should not trigger another refresh.
    assert credential.get_token() == "token-1"
    assert len(calls) == 1


def test_oauth_credential_refreshes_after_expiry(monkeypatch):
    responses = iter(
        [
            _make_response({"access_token": "token-1", "expires_in": 7200}),
            _make_response({"access_token": "token-2", "expires_in": 7200}),
        ]
    )
    monkeypatch.setattr(
        "cartography.intel.bitbucket.auth.requests.post",
        lambda *args, **kwargs: next(responses),
    )

    credential = OAuth2RefreshCredential("client-id", "client-secret", "refresh-token")
    assert credential.get_token() == "token-1"

    # Force the cached token to look expired.
    credential._token_expires_at = 0
    assert credential.get_token() == "token-2"


def test_make_credential_unknown_method_raises():
    with pytest.raises(ValueError, match="Unsupported"):
        make_credential("tokn", "my-token", None, None, None)


def test_oauth_credential_uses_rotated_refresh_token(monkeypatch):
    sent_refresh_tokens = []
    responses = iter(
        [
            {"access_token": "token-1", "expires_in": 7200, "refresh_token": "rt-2"},
            {"access_token": "token-2", "expires_in": 7200},
        ]
    )

    def _post(url, data=None, auth=None, timeout=None):
        sent_refresh_tokens.append(data["refresh_token"])
        return _make_response(next(responses))

    monkeypatch.setattr("cartography.intel.bitbucket.auth.requests.post", _post)

    credential = OAuth2RefreshCredential("client-id", "client-secret", "rt-1")
    credential.get_token()
    credential._token_expires_at = 0
    credential.get_token()

    assert sent_refresh_tokens == ["rt-1", "rt-2"]
