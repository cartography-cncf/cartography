import json

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


def test_transform_accepts_key_unknown_to_the_okta_sdk() -> None:
    # Arrange
    authenticator = {
        "id": "aut-custom-otp",
        "key": "custom_otp",
        "name": "Custom OTP Authenticator",
        "status": "INACTIVE",
        "type": "security_key",
        "created": "2025-01-01T00:00:00.000Z",
        "lastUpdated": "2025-01-02T00:00:00.000Z",
    }

    # Act
    result = _transform_okta_authenticators([authenticator])

    # Assert
    assert result == [
        {
            "id": "aut-custom-otp",
            "created": "2025-01-01T00:00:00.000Z",
            "key": "custom_otp",
            "last_updated": "2025-01-02T00:00:00.000Z",
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
