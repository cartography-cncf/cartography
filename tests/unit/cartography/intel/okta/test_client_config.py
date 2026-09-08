from cartography.config import Config
from cartography.intel.okta import _build_okta_client_config
from cartography.intel.okta import OKTA_OAUTH_SCOPES


def _config(**kwargs) -> Config:
    return Config(
        neo4j_uri="bolt://localhost:7687",
        okta_org_id="test-org",
        **kwargs,
    )


def test_oauth_client_credentials_config():
    config = _config(okta_client_id="0oa123", okta_private_key='{"kty": "RSA"}')
    client_config = _build_okta_client_config(config)
    assert client_config == {
        "orgUrl": "https://test-org.okta.com",
        "authorizationMode": "PrivateKey",
        "clientId": "0oa123",
        "privateKey": '{"kty": "RSA"}',
        "scopes": OKTA_OAUTH_SCOPES,
    }


def test_oauth_with_dpop_enabled():
    config = _config(
        okta_client_id="0oa123",
        okta_private_key='{"kty": "RSA"}',
        okta_dpop=True,
    )
    client_config = _build_okta_client_config(config)
    assert client_config is not None
    assert client_config["dpopEnabled"] is True


def test_ssws_api_key_config():
    config = _config(okta_api_key="00sekrit")
    client_config = _build_okta_client_config(config)
    assert client_config == {
        "orgUrl": "https://test-org.okta.com",
        "token": "00sekrit",
    }


def test_oauth_takes_precedence_over_api_key():
    config = _config(
        okta_api_key="00sekrit",
        okta_client_id="0oa123",
        okta_private_key='{"kty": "RSA"}',
    )
    client_config = _build_okta_client_config(config)
    assert client_config is not None
    assert client_config["authorizationMode"] == "PrivateKey"
    assert "token" not in client_config


def test_no_credentials_returns_none():
    assert _build_okta_client_config(_config()) is None


def test_partial_oauth_credentials_returns_none():
    # client id without a private key must not half-configure OAuth
    assert _build_okta_client_config(_config(okta_client_id="0oa123")) is None


def test_custom_base_domain():
    config = _config(okta_api_key="00sekrit", okta_base_domain="oktapreview.com")
    client_config = _build_okta_client_config(config)
    assert client_config is not None
    assert client_config["orgUrl"] == "https://test-org.oktapreview.com"
