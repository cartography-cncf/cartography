import asyncio
import json
from datetime import datetime
from datetime import timezone
from typing import Any
from unittest.mock import MagicMock

from cartography.intel.okta.authenticators import _get_okta_authenticators
from cartography.intel.okta.authenticators import _transform_okta_authenticators


def test_transform_accepts_email_authenticator_without_provider() -> None:
    # Arrange
    authenticator = {
        "id": "aut-email",
        "key": "okta_email",
        "name": "Email",
        "settings": {"allowedFor": "any", "compliance": {"fips": "OPTIONAL"}},
        "status": "ACTIVE",
        "type": "email",
    }

    # Act
    result = _transform_okta_authenticators([authenticator])

    # Assert
    assert result[0]["id"] == "aut-email"
    assert result[0]["settings_allowed_for"] == "any"
    assert result[0]["settings_compliance"] == '{"fips": "OPTIONAL"}'
    assert "provider_type" not in result[0]


class _RawPageExecutor:
    def __init__(self, pages: dict[str, list[dict[str, Any]]]) -> None:
        self.pages = pages

    async def create_request(self, method, url, body, headers):
        return url, None

    async def execute(self, url):
        response = MagicMock()
        response.links = {}
        return response, json.dumps(self.pages[url]), None


def test_get_and_transform_accept_key_unknown_to_the_okta_sdk() -> None:
    # Arrange
    okta_client = MagicMock()
    okta_client.list_authenticators.side_effect = AssertionError(
        "typed SDK model rejects unknown authenticator keys",
    )
    okta_client.get_request_executor.return_value = _RawPageExecutor(
        {
            "/api/v1/authenticators": [
                {
                    "id": "aut-custom-otp",
                    "key": "custom_otp",
                    "name": "Custom OTP Authenticator",
                    "status": "INACTIVE",
                    "type": "security_key",
                    "created": "2025-01-01T00:00:00.000Z",
                    "lastUpdated": "2025-01-02T00:00:00.000Z",
                },
            ],
        },
    )

    # Act
    result = _transform_okta_authenticators(
        asyncio.run(_get_okta_authenticators(okta_client)),
    )

    # Assert
    assert result == [
        {
            "id": "aut-custom-otp",
            "created": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "key": "custom_otp",
            "last_updated": datetime(2025, 1, 2, tzinfo=timezone.utc),
            "name": "Custom OTP Authenticator",
            "status": "INACTIVE",
            "authenticator_type": "security_key",
        },
    ]


def test_transform_does_not_persist_provider_secrets() -> None:
    # Arrange
    authenticator = {
        "id": "aut-radius",
        "key": "security_question",
        "name": "RADIUS",
        "provider": {
            "type": "RADIUS",
            "configuration": {
                "hostName": "radius.example.com",
                "secretKey": "secret-key",
                "sharedSecret": "shared-secret",
            },
        },
        "status": "ACTIVE",
        "type": "security_question",
    }

    # Act
    result = _transform_okta_authenticators([authenticator])

    # Assert
    assert json.loads(result[0]["provider_configuration"]) == {
        "hostName": "radius.example.com"
    }
    assert "provider_secret_key" not in result[0]
    assert "provider_shared_secret" not in result[0]
