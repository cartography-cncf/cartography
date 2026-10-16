import asyncio
import base64
import json
import logging
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from okta.errors.okta_api_error import OktaAPIError

from cartography.config import Config
from cartography.intel import okta
from cartography.intel.okta.common import collect_paginated
from cartography.intel.okta.common import is_oauth_token_error
from cartography.intel.okta.common import OKTA_OAUTH_DEFAULT_SCOPES
from cartography.intel.okta.common import OktaApiError

PRIVATE_KEY_PEM = (
    rsa.generate_private_key(public_exponent=65537, key_size=2048)
    .private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    .decode()
)


def _config(**kwargs: Any) -> Config:
    return Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=1,
        okta_org_id="acme",
        **kwargs,
    )


def _jwt_header(token: str) -> dict[str, Any]:
    header = token.split(".")[0]
    return json.loads(base64.urlsafe_b64decode(header + "=" * (-len(header) % 4)))


def test_create_okta_client_uses_api_token() -> None:
    # Act
    client = okta.create_okta_client(_config(okta_api_key="00token"))

    # Assert
    client_config = client._config["client"]
    assert client_config["orgUrl"] == "https://acme.okta.com"
    assert client_config["authorizationMode"] == "SSWS"
    assert client_config["token"] == "00token"


def test_create_okta_client_uses_oauth_service_app() -> None:
    # Act
    client = okta.create_okta_client(
        _config(
            okta_client_id="0oaclient",
            okta_private_key=PRIVATE_KEY_PEM,
            okta_private_key_id="key-1",
        ),
    )

    # Assert
    client_config = client._config["client"]
    assert client_config["authorizationMode"] == "PrivateKey"
    assert client_config["clientId"] == "0oaclient"
    assert client_config["scopes"] == list(OKTA_OAUTH_DEFAULT_SCOPES)
    assert client_config["dpopEnabled"] is True
    oauth = client.get_request_executor()._oauth
    assert oauth.is_dpop_enabled()
    # The client assertion is signed with the configured key and names its kid.
    assert _jwt_header(oauth.get_JWT())["kid"] == "key-1"


def test_create_okta_client_honors_scope_and_dpop_overrides() -> None:
    # Act
    client = okta.create_okta_client(
        _config(
            okta_client_id="0oaclient",
            okta_private_key=PRIVATE_KEY_PEM,
            okta_scopes="okta.users.read, okta.groups.read okta.apps.read",
            okta_dpop_enabled=False,
        ),
    )

    # Assert
    client_config = client._config["client"]
    assert client_config["scopes"] == [
        "okta.users.read",
        "okta.groups.read",
        "okta.apps.read",
    ]
    assert not client.get_request_executor()._oauth.is_dpop_enabled()


def test_create_okta_client_prefers_oauth_over_api_token(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Act
    with caplog.at_level(logging.WARNING):
        client = okta.create_okta_client(
            _config(
                okta_api_key="00token",
                okta_client_id="0oaclient",
                okta_private_key=PRIVATE_KEY_PEM,
            ),
        )

    # Assert
    assert client._config["client"]["authorizationMode"] == "PrivateKey"
    assert "using the OAuth client" in caplog.text


def test_oauth_token_failure_raises_oauth_token_error() -> None:
    # Arrange
    client = okta.create_okta_client(
        _config(okta_client_id="0oaclient", okta_private_key=PRIVATE_KEY_PEM),
    )
    token_error = OktaAPIError(
        "https://acme.okta.com/oauth2/v1/token",
        None,
        {
            "errorCode": "invalid_scope",
            "errorSummary": "The following scopes are not allowed: okta.logStreams.read",
        },
    )
    client.get_request_executor()._oauth.get_oauth_token = AsyncMock(
        return_value=(None, "Bearer", token_error),
    )

    # Act
    with pytest.raises(OktaApiError) as exc_info:
        asyncio.run(collect_paginated(client.list_users))

    # Assert
    assert exc_info.value.error_code == "invalid_scope"
    assert is_oauth_token_error(exc_info.value)


def test_start_okta_ingestion_skips_without_complete_credentials(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Arrange: a client ID without its private key is not usable.
    create_client = MagicMock()
    monkeypatch.setattr(okta, "create_okta_client", create_client)

    # Act
    with caplog.at_level(logging.WARNING):
        okta.start_okta_ingestion(MagicMock(), _config(okta_client_id="0oaclient"))

    # Assert
    create_client.assert_not_called()
    assert "incomplete OAuth settings" in caplog.text
