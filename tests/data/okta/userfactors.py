from unittest.mock import MagicMock

from okta.models.user_factor import UserFactor


def create_test_factor():
    """Create a mock UserFactor object for testing."""
    factor = MagicMock(spec=UserFactor)

    factor.id = "factor_id_value"
    factor.factor_type = "factor_type_value"
    factor.provider = "factor_provider_value"
    factor.status = "factor_status_value"
    factor.created = None
    factor.last_updated = None

    return factor


# Okta sets FULFILLMENT_PENDING / FULFILLMENT_ERRORED on WebAuthn preregistration
# factors, but SDK 3.4.4 does not declare those values in UserFactorStatus.
WEBAUTHN_FACTOR_WITH_FULFILLMENT_ERRORED_STATUS = {
    "id": "fwf1prereg0Xy3Zq5d7",
    "factorType": "webauthn",
    "provider": "FIDO",
    "vendorName": "FIDO",
    "status": "FULFILLMENT_ERRORED",
    "created": "2026-08-31T10:11:12.000Z",
    "lastUpdated": "2026-09-01T13:14:15.000Z",
    "profile": {
        "credentialId": "credential-id-value",
        "authenticatorName": "YubiKey 5 NFC",
    },
}

SMS_FACTOR_WITH_ACTIVE_STATUS = {
    "id": "sms1standard0Ab2Cd4",
    "factorType": "sms",
    "provider": "OKTA",
    "vendorName": "OKTA",
    "status": "ACTIVE",
    "created": "2026-08-31T10:11:12.000Z",
    "lastUpdated": "2026-09-01T13:14:15.000Z",
    "profile": {"phoneNumber": "+15555550100"},
}
