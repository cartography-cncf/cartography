import asyncio
import json
import logging
from dataclasses import dataclass
from dataclasses import field
from functools import cache
from typing import Any
from unittest.mock import MagicMock

import jwt
import okta.dpop
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from okta.http_client import HTTPClient

from cartography.config import Config
from cartography.intel import okta as okta_intel
from cartography.intel.okta.common import _load_dpop_signing_key
from cartography.intel.okta.common import get_raw_json
from cartography.intel.okta.common import is_oauth_token_error
from cartography.intel.okta.common import OKTA_OAUTH_DEFAULT_SCOPES
from cartography.intel.okta.common import OktaApiError

TOKEN_URL = "https://acme.okta.com/oauth2/v1/token"
ORG_URL = "https://acme.okta.com/api/v1/org"


@cache
def _private_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _private_key_pem() -> str:
    return (
        _private_key()
        .private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        .decode()
    )


@dataclass
class _Response:
    status: int
    body: dict[str, Any]
    content_type: str = "application/json"
    headers: dict[str, str] = field(default_factory=dict)
    links: dict[str, Any] = field(default_factory=dict)


@dataclass
class _Request:
    url: str
    headers: dict[str, str]
    form: dict[str, str]


class _FakeOktaApi:
    """
    Stands in for Okta's HTTP API at the SDK transport, so tests see the
    requests Cartography's client actually sends.
    """

    def __init__(self) -> None:
        self.requests: list[_Request] = []
        self.token_error: dict[str, str] | None = None

    def reject_token(self, error: str, description: str) -> None:
        self.token_error = {"error": error, "error_description": description}

    async def send_request(
        self,
        http_client: HTTPClient,
        request: dict[str, Any],
    ) -> tuple[None, _Response, str, None]:
        headers = {**http_client._default_headers, **request["headers"]}
        self.requests.append(
            _Request(request["url"], headers, request.get("form") or {}),
        )
        if request["url"] != TOKEN_URL:
            response = _Response(200, {})
        elif self.token_error:
            response = _Response(400, self.token_error)
        else:
            # Okta binds the token with DPoP when the request carries a proof.
            token_type = "DPoP" if "DPoP" in headers else "Bearer"
            response = _Response(
                200,
                {
                    "access_token": "fake-access-token",
                    "token_type": token_type,
                    "expires_in": 3600,
                },
            )
        return None, response, json.dumps(response.body), None


@pytest.fixture
def okta_api(monkeypatch):
    api = _FakeOktaApi()

    async def send_request(http_client: HTTPClient, request: dict[str, Any]):
        return await api.send_request(http_client, request)

    monkeypatch.setattr(HTTPClient, "send_request", send_request)
    # The SDK generates a 3072-bit DPoP key per client, which takes seconds.
    monkeypatch.setattr(okta.dpop, "RSA_KEY_SIZE_BITS", 2048)
    return api


def _config(**kwargs: Any) -> Config:
    return Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=1,
        okta_org_id="acme",
        **kwargs,
    )


def _oauth_config(**kwargs: Any) -> Config:
    return _config(
        okta_client_id="0oaclient",
        okta_private_key=_private_key_pem(),
        **kwargs,
    )


def _fetch_org(config: Config) -> None:
    client = okta_intel.create_okta_client(config)
    asyncio.run(get_raw_json(client, "/api/v1/org"))


def _dpop_proof_claims(proof: str) -> dict[str, Any]:
    public_key = jwt.PyJWK(jwt.get_unverified_header(proof)["jwk"], "RS256").key
    return jwt.decode(proof, public_key, algorithms=["RS256"])


def test_api_token_authenticates_with_ssws(okta_api: _FakeOktaApi) -> None:
    # Act
    _fetch_org(_config(okta_api_key="00token"))

    # Assert
    (request,) = okta_api.requests
    assert request.url == ORG_URL
    assert request.headers["Authorization"] == "SSWS 00token"


def test_oauth_token_request_is_signed_with_the_service_app_key(
    okta_api: _FakeOktaApi,
) -> None:
    # Act
    _fetch_org(_oauth_config(okta_private_key_id="key-1"))

    # Assert
    token_request, _ = okta_api.requests
    assert token_request.url == TOKEN_URL
    assert token_request.form["grant_type"] == "client_credentials"
    assertion = token_request.form["client_assertion"]
    assert jwt.get_unverified_header(assertion)["kid"] == "key-1"
    claims = jwt.decode(
        assertion,
        _private_key().public_key(),
        algorithms=["RS256"],
        audience=TOKEN_URL,
    )
    assert claims["iss"] == "0oaclient"
    assert claims["sub"] == "0oaclient"


def test_oauth_token_request_asks_for_the_default_scopes(
    okta_api: _FakeOktaApi,
) -> None:
    # Act
    _fetch_org(_oauth_config())

    # Assert
    token_request, _ = okta_api.requests
    assert token_request.form["scope"] == " ".join(OKTA_OAUTH_DEFAULT_SCOPES)


def test_oauth_token_request_asks_for_configured_scopes(
    okta_api: _FakeOktaApi,
) -> None:
    # Act
    _fetch_org(_oauth_config(okta_scopes="okta.users.read,okta.groups.read"))

    # Assert
    token_request, _ = okta_api.requests
    assert token_request.form["scope"] == "okta.users.read okta.groups.read"


def test_oauth_requests_are_bound_with_dpop_by_default(
    okta_api: _FakeOktaApi,
) -> None:
    # Act
    _fetch_org(_oauth_config())

    # Assert
    token_request, api_request = okta_api.requests
    assert "DPoP" in token_request.headers
    assert api_request.headers["Authorization"] == "DPoP fake-access-token"
    proof_claims = _dpop_proof_claims(api_request.headers["DPoP"])
    assert proof_claims["htm"] == "GET"
    assert proof_claims["htu"] == ORG_URL


def test_oauth_requests_use_bearer_tokens_when_dpop_is_disabled(
    okta_api: _FakeOktaApi,
) -> None:
    # Act
    _fetch_org(_oauth_config(okta_dpop_enabled=False))

    # Assert
    token_request, api_request = okta_api.requests
    assert "DPoP" not in token_request.headers
    assert api_request.headers["Authorization"] == "Bearer fake-access-token"


def test_oauth_client_is_used_when_an_api_token_is_also_set(
    okta_api: _FakeOktaApi,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Act
    with caplog.at_level(logging.WARNING):
        _fetch_org(_oauth_config(okta_api_key="00token", okta_dpop_enabled=False))

    # Assert
    _, api_request = okta_api.requests
    assert api_request.headers["Authorization"] == "Bearer fake-access-token"
    assert "using the OAuth client" in caplog.text


def test_rejected_token_request_raises_an_oauth_token_error(
    okta_api: _FakeOktaApi,
) -> None:
    # Arrange: Okta refuses the token only when it grants none of the scopes.
    okta_api.reject_token(
        "consent_required",
        "You are not allowed any of the requested scopes.",
    )

    # Act
    with pytest.raises(OktaApiError) as exc_info:
        _fetch_org(_oauth_config(okta_dpop_enabled=False))

    # Assert
    assert exc_info.value.error_code == "consent_required"
    assert is_oauth_token_error(exc_info.value)


def test_start_okta_ingestion_explains_a_rejected_token_request(
    okta_api: _FakeOktaApi,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Arrange
    okta_api.reject_token("invalid_dpop_proof", "The DPoP proof JWT header is missing.")

    # Act
    with caplog.at_level(logging.ERROR), pytest.raises(OktaApiError):
        okta_intel.start_okta_ingestion(
            MagicMock(),
            _oauth_config(okta_dpop_enabled=False),
        )

    # Assert
    assert "OAuth access token (invalid_dpop_proof)" in caplog.text


def test_start_okta_ingestion_skips_without_an_org_id(
    okta_api: _FakeOktaApi,
) -> None:
    # Arrange
    config = _config(okta_api_key="00token")
    config.okta_org_id = None

    # Act
    okta_intel.start_okta_ingestion(MagicMock(), config)

    # Assert
    assert okta_api.requests == []


def test_dpop_proofs_are_signed_without_reparsing_the_key(
    okta_api: _FakeOktaApi,
) -> None:
    # Arrange
    _load_dpop_signing_key.cache_clear()
    generator = okta.dpop.DPoPProofGenerator({"dpopKeyRotationInterval": 86400})

    # Act
    first = generator.generate_proof_jwt("GET", ORG_URL, access_token="token")
    second = generator.generate_proof_jwt("GET", ORG_URL, access_token="token")

    # Assert
    assert _load_dpop_signing_key.cache_info().misses == 1
    assert _dpop_proof_claims(first)["htu"] == ORG_URL
    assert _dpop_proof_claims(second)["htu"] == ORG_URL
