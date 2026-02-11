from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.github.app_auth import AppCredential
from cartography.intel.github.app_auth import make_credential
from cartography.intel.github.app_auth import PatCredential


def test_pat_get_token_returns_static_token() -> None:
    cred = PatCredential("ghp_abc123")
    assert cred.get_token() == "ghp_abc123"


def test_pat_get_token_is_stable() -> None:
    cred = PatCredential("ghp_abc123")
    assert cred.get_token() == cred.get_token()


@patch("cartography.intel.github.app_auth.requests.post")
@patch("cartography.intel.github.app_auth.jwt.encode")
def test_app_get_token_fetches_installation_token(
    mock_jwt_encode: MagicMock,
    mock_post: MagicMock,
) -> None:
    mock_jwt_encode.return_value = "fake-jwt"
    mock_response = MagicMock()
    mock_response.json.return_value = {"token": "ghs_install_token_123"}
    mock_post.return_value = mock_response

    cred = AppCredential(
        client_id="Iv1.abc",
        private_key="-----BEGIN RSA PRIVATE KEY-----\nfake\n-----END RSA PRIVATE KEY-----",
        installation_id="12345",
    )
    token = cred.get_token()

    assert token == "ghs_install_token_123"
    mock_jwt_encode.assert_called_once()
    mock_post.assert_called_once()
    # Verify the installation token URL
    call_args = mock_post.call_args
    assert "/app/installations/12345/access_tokens" in call_args[0][0]


@patch("cartography.intel.github.app_auth.requests.post")
@patch("cartography.intel.github.app_auth.jwt.encode")
def test_app_token_is_cached_until_near_expiry(
    mock_jwt_encode: MagicMock,
    mock_post: MagicMock,
) -> None:
    mock_jwt_encode.return_value = "fake-jwt"
    mock_response = MagicMock()
    mock_response.json.return_value = {"token": "ghs_token"}
    mock_post.return_value = mock_response

    cred = AppCredential(
        client_id="Iv1.abc",
        private_key="fake-key",
        installation_id="12345",
    )

    # First call fetches token
    cred.get_token()
    assert mock_post.call_count == 1

    # Second call uses cached token (not near expiry)
    cred.get_token()
    assert mock_post.call_count == 1


@patch("cartography.intel.github.app_auth.requests.post")
@patch("cartography.intel.github.app_auth.jwt.encode")
@patch("cartography.intel.github.app_auth.time.time")
def test_app_token_refreshes_when_near_expiry(
    mock_time: MagicMock,
    mock_jwt_encode: MagicMock,
    mock_post: MagicMock,
) -> None:
    mock_jwt_encode.return_value = "fake-jwt"
    mock_response = MagicMock()
    mock_response.json.return_value = {"token": "ghs_token"}
    mock_post.return_value = mock_response

    # Start at time 1000
    mock_time.return_value = 1000

    cred = AppCredential(
        client_id="Iv1.abc",
        private_key="fake-key",
        installation_id="12345",
    )

    cred.get_token()
    assert mock_post.call_count == 1

    # Jump to near expiry (1000 + 3600 - 300 = 4300, so time >= 4300 triggers refresh)
    mock_time.return_value = 4300
    cred.get_token()
    assert mock_post.call_count == 2


@patch("cartography.intel.github.app_auth.requests.post")
@patch("cartography.intel.github.app_auth.jwt.encode")
def test_app_github_enterprise_url(
    mock_jwt_encode: MagicMock,
    mock_post: MagicMock,
) -> None:
    mock_jwt_encode.return_value = "fake-jwt"
    mock_response = MagicMock()
    mock_response.json.return_value = {"token": "ghs_token"}
    mock_post.return_value = mock_response

    cred = AppCredential(
        client_id="Iv1.abc",
        private_key="fake-key",
        installation_id="12345",
        api_base_url="https://github.example.com/api/v3",
    )
    cred.get_token()

    call_url = mock_post.call_args[0][0]
    assert (
        call_url
        == "https://github.example.com/api/v3/app/installations/12345/access_tokens"
    )


@patch("cartography.intel.github.app_auth.jwt.encode")
def test_app_jwt_payload(mock_jwt_encode: MagicMock) -> None:
    mock_jwt_encode.return_value = "fake-jwt"

    cred = AppCredential(
        client_id="Iv1.myclientid",
        private_key="fake-key",
        installation_id="12345",
    )

    with patch("cartography.intel.github.app_auth.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"token": "ghs_token"}
        mock_post.return_value = mock_response
        cred.get_token()

    # Verify JWT was created with correct payload
    call_args = mock_jwt_encode.call_args
    payload = call_args[0][0]
    assert payload["iss"] == "Iv1.myclientid"
    assert "iat" in payload
    assert "exp" in payload
    assert payload["exp"] - payload["iat"] == 600  # 10 minute expiry
    assert call_args[1]["algorithm"] == "RS256"


def test_make_credential_pat_config() -> None:
    auth_data = {
        "token": "ghp_abc123",
        "url": "https://api.github.com/graphql",
        "name": "my-org",
    }
    cred = make_credential(auth_data)
    assert isinstance(cred, PatCredential)
    assert cred.get_token() == "ghp_abc123"


def test_make_credential_app_config() -> None:
    auth_data = {
        "client_id": "Iv1.abc",
        "private_key": "fake-key",
        "installation_id": "12345",
        "url": "https://api.github.com/graphql",
        "name": "my-org",
    }
    cred = make_credential(auth_data)
    assert isinstance(cred, AppCredential)


def test_make_credential_app_config_enterprise() -> None:
    auth_data = {
        "client_id": "Iv1.abc",
        "private_key": "fake-key",
        "installation_id": "12345",
        "url": "https://github.example.com/api/graphql",
        "name": "my-org",
    }
    cred = make_credential(auth_data)
    assert isinstance(cred, AppCredential)
    assert cred._api_base_url == "https://github.example.com/api/v3"


def test_make_credential_app_missing_keys_raises() -> None:
    auth_data = {
        "client_id": "Iv1.abc",
        "url": "https://api.github.com/graphql",
        "name": "my-org",
    }
    with pytest.raises(ValueError, match="missing required keys"):
        make_credential(auth_data)


def test_make_credential_invalid_config_raises() -> None:
    auth_data = {
        "url": "https://api.github.com/graphql",
        "name": "my-org",
    }
    with pytest.raises(ValueError, match="must contain either"):
        make_credential(auth_data)
