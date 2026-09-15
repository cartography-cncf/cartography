import json
from types import SimpleNamespace
from typing import Any

from cartography.intel.okta.authenticators import _transform_okta_authenticators


def test_transform_accepts_email_authenticator_without_provider() -> None:
    # Arrange
    authenticator: Any = SimpleNamespace(
        id="aut-email",
        created=None,
        key="okta_email",
        last_updated=None,
        name="Email",
        settings=SimpleNamespace(
            to_dict=lambda: {
                "allowedFor": "any",
                "compliance": {"fips": "OPTIONAL"},
            }
        ),
        status="ACTIVE",
        type="email",
    )

    # Act
    result = _transform_okta_authenticators([authenticator])

    # Assert
    assert result[0]["id"] == "aut-email"
    assert result[0]["settings_allowed_for"] == "any"
    assert result[0]["settings_compliance"] == '{"fips": "OPTIONAL"}'
    assert "provider_type" not in result[0]


def test_transform_does_not_persist_provider_secrets() -> None:
    # Arrange
    authenticator: Any = SimpleNamespace(
        id="aut-radius",
        created=None,
        key="security_question",
        last_updated=None,
        name="RADIUS",
        provider=SimpleNamespace(
            type="RADIUS",
            configuration=SimpleNamespace(
                to_dict=lambda: {
                    "hostName": "radius.example.com",
                    "secretKey": "secret-key",
                    "sharedSecret": "shared-secret",
                }
            ),
        ),
        status="ACTIVE",
        type="security_question",
    )

    # Act
    result = _transform_okta_authenticators([authenticator])

    # Assert
    assert json.loads(result[0]["provider_configuration"]) == {
        "hostName": "radius.example.com"
    }
    assert "provider_secret_key" not in result[0]
    assert "provider_shared_secret" not in result[0]
