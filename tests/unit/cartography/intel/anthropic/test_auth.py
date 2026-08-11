from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests

from cartography.intel.anthropic.auth import AnthropicAuth
from cartography.intel.anthropic.auth import ApiKeyCredential
from cartography.intel.anthropic.auth import EnvVarAssertionSource
from cartography.intel.anthropic.auth import FileAssertionSource
from cartography.intel.anthropic.auth import is_federated
from cartography.intel.anthropic.auth import make_assertion_source
from cartography.intel.anthropic.auth import make_credential
from cartography.intel.anthropic.auth import WorkloadIdentityCredential


def _token_response(access_token: str = "sk-ant-oat01-abc", expires_in: int = 3600):
    response = MagicMock()
    response.json.return_value = {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "scope": "org:admin",
    }
    return response


def _wif_credential(assertion_source, workspace_id: str | None = None):
    return WorkloadIdentityCredential(
        assertion_source=assertion_source,
        federation_rule_id="fdrl_123",
        organization_id="8834c225-ea27-405a-aea9-5ed5f07f4858",
        service_account_id="svac_456",
        workspace_id=workspace_id,
    )


def test_apikey_credential_uses_x_api_key_header() -> None:
    cred = ApiKeyCredential("sk-ant-admin01-abc")
    assert cred.get_headers() == {"X-Api-Key": "sk-ant-admin01-abc"}


def test_file_assertion_source_is_reread_on_each_call(tmp_path: Path) -> None:
    # Kubernetes rotates projected service account tokens on disk, so a value cached
    # at startup goes stale mid-sync.
    token_file = tmp_path / "token"
    token_file.write_text("first-jwt\n")
    source = FileAssertionSource(str(token_file))
    assert source.read() == "first-jwt"

    token_file.write_text("rotated-jwt\n")
    assert source.read() == "rotated-jwt"


def test_env_var_assertion_source_reads_and_strips(monkeypatch) -> None:
    monkeypatch.setenv("MY_IDENTITY_TOKEN", "  a-jwt  ")
    assert EnvVarAssertionSource("MY_IDENTITY_TOKEN").read() == "a-jwt"


def test_env_var_assertion_source_raises_when_unset(monkeypatch) -> None:
    monkeypatch.delenv("MY_IDENTITY_TOKEN", raising=False)
    with pytest.raises(ValueError, match="does not contain an identity token"):
        EnvVarAssertionSource("MY_IDENTITY_TOKEN").read()


@patch("cartography.intel.anthropic.auth.requests.post")
def test_wif_exchange_posts_jwt_bearer_grant(mock_post: MagicMock) -> None:
    mock_post.return_value = _token_response()
    source = MagicMock()
    source.read.return_value = "the-oidc-jwt"

    headers = _wif_credential(source).get_headers()

    assert headers == {"Authorization": "Bearer sk-ant-oat01-abc"}
    assert "X-Api-Key" not in headers
    url = mock_post.call_args[0][0]
    assert url == "https://api.anthropic.com/v1/oauth/token"
    assert mock_post.call_args.kwargs["json"] == {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": "the-oidc-jwt",
        "federation_rule_id": "fdrl_123",
        "organization_id": "8834c225-ea27-405a-aea9-5ed5f07f4858",
        "service_account_id": "svac_456",
    }


@patch("cartography.intel.anthropic.auth.requests.post")
def test_wif_exchange_sends_workspace_id_when_set(mock_post: MagicMock) -> None:
    mock_post.return_value = _token_response()
    source = MagicMock()
    source.read.return_value = "the-oidc-jwt"

    _wif_credential(source, workspace_id="wrkspc_789").get_headers()

    assert mock_post.call_args.kwargs["json"]["workspace_id"] == "wrkspc_789"


@patch("cartography.intel.anthropic.auth.requests.post")
def test_wif_token_is_cached_until_near_expiry(mock_post: MagicMock) -> None:
    mock_post.return_value = _token_response()
    source = MagicMock()
    source.read.return_value = "the-oidc-jwt"
    cred = _wif_credential(source)

    cred.get_headers()
    cred.get_headers()

    mock_post.assert_called_once()


@patch("cartography.intel.anthropic.auth.requests.post")
def test_wif_token_refreshes_and_rereads_assertion(mock_post: MagicMock) -> None:
    # A token inside the refresh buffer must be re-exchanged, and the exchange must
    # pull a fresh assertion rather than replaying the one used the first time.
    mock_post.side_effect = [
        _token_response("first-token", expires_in=10),
        _token_response("second-token"),
    ]
    source = MagicMock()
    source.read.side_effect = ["first-jwt", "second-jwt"]
    cred = _wif_credential(source)

    assert cred.get_headers() == {"Authorization": "Bearer first-token"}
    assert cred.get_headers() == {"Authorization": "Bearer second-token"}

    assert source.read.call_count == 2
    assert mock_post.call_args_list[1].kwargs["json"]["assertion"] == "second-jwt"


@patch("cartography.intel.anthropic.auth.requests.post")
def test_auth_applies_headers_to_request(mock_post: MagicMock) -> None:
    mock_post.return_value = _token_response()
    source = MagicMock()
    source.read.return_value = "the-oidc-jwt"

    auth = AnthropicAuth(_wif_credential(source))
    request = requests.Request("GET", "https://api.anthropic.com/v1/organizations/me")
    prepared = auth(request.prepare())

    assert prepared.headers["Authorization"] == "Bearer sk-ant-oat01-abc"


def test_make_credential_returns_apikey_credential() -> None:
    cred = make_credential(apikey="sk-ant-admin01-abc")
    assert isinstance(cred, ApiKeyCredential)
    assert not is_federated(cred)


def test_make_credential_prefers_wif_over_apikey(tmp_path: Path) -> None:
    # Federation reaches strictly more endpoints than an Admin API key, so it wins.
    token_file = tmp_path / "token"
    token_file.write_text("a-jwt")
    cred = make_credential(
        apikey="sk-ant-admin01-abc",
        identity_token_file=str(token_file),
        federation_rule_id="fdrl_123",
        organization_id="org-uuid",
        service_account_id="svac_456",
    )
    assert isinstance(cred, WorkloadIdentityCredential)
    assert is_federated(cred)


def test_make_credential_raises_on_partial_wif_config(tmp_path: Path) -> None:
    token_file = tmp_path / "token"
    token_file.write_text("a-jwt")
    with pytest.raises(ValueError, match="partially configured"):
        make_credential(
            identity_token_file=str(token_file),
            federation_rule_id="fdrl_123",
        )


def test_make_credential_raises_when_nothing_configured() -> None:
    with pytest.raises(ValueError, match="not configured"):
        make_credential()


def test_make_assertion_source_returns_none_when_unconfigured() -> None:
    assert make_assertion_source(None, None) is None


def test_make_assertion_source_rejects_both_sources() -> None:
    with pytest.raises(ValueError, match="mutually exclusive"):
        make_assertion_source("/path/to/token", "MY_IDENTITY_TOKEN")
