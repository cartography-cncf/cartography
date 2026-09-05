import json
from copy import deepcopy
from typing import Any

from okta.models.application_json_converter import ApplicationJsonConverter
from okta.models.user_factor import UserFactor

import cartography.intel.okta.common  # noqa: F401
from tests.data.okta.application import APPLICATION_WITH_REDITECT_URIS
from tests.data.okta.application import BOOKMARK_APPLICATION_WITHOUT_URL
from tests.data.okta.application import OIN_BROWSER_PLUGIN_APPLICATION
from tests.data.okta.application import SAML_APPLICATION_WITH_UNKNOWN_FEATURE
from tests.data.okta.userfactors import SMS_FACTOR_WITH_ACTIVE_STATUS
from tests.data.okta.userfactors import WEBAUTHN_FACTOR_WITH_FULFILLMENT_ERRORED_STATUS


def test_saml_application_accepts_omitted_optional_booleans() -> None:
    # Arrange
    payload: dict[str, Any] = deepcopy(SAML_APPLICATION_WITH_UNKNOWN_FEATURE)
    sign_on = payload["settings"]["signOn"]
    for field_name in (
        "allowMultipleAcsEndpoints",
        "assertionSigned",
        "honorForceAuthn",
        "requestCompressed",
        "responseSigned",
    ):
        del sign_on[field_name]

    # Act
    application = ApplicationJsonConverter.from_dict(payload)

    # Assert
    assert application is not None
    assert application.id == "0oaFeatures"
    assert application.settings.sign_on.allow_multiple_acs_endpoints is None
    assert application.settings.sign_on.assertion_signed is None
    assert application.settings.sign_on.honor_force_authn is None
    assert application.settings.sign_on.request_compressed is None
    assert application.settings.sign_on.response_signed is None


def test_saml_application_preserves_unknown_feature() -> None:
    # Act
    application = ApplicationJsonConverter.from_dict(
        SAML_APPLICATION_WITH_UNKNOWN_FEATURE,
    )

    # Assert
    assert application is not None
    assert application.features == [
        "PUSH_NEW_USERS",
        "AUTO_CONFIRM_IMPORTS",
        "SCIM_PROVISIONING",
    ]


def test_browser_plugin_application_accepts_oin_catalog_shape() -> None:
    # Act
    application = ApplicationJsonConverter.from_dict(OIN_BROWSER_PLUGIN_APPLICATION)

    # Assert
    assert application is not None
    assert application.id == "0oaOinSwa"
    assert application.name == "docusign"
    assert application.settings.app is None


def test_bookmark_application_accepts_omitted_url() -> None:
    # Act
    application = ApplicationJsonConverter.from_dict(BOOKMARK_APPLICATION_WITHOUT_URL)

    # Assert
    assert application is not None
    assert application.id == "0oaBookmark"
    assert application.settings.app.url is None


def test_openid_connect_application_accepts_omitted_grant_types() -> None:
    # Arrange
    payload = json.loads(APPLICATION_WITH_REDITECT_URIS)
    del payload["settings"]["oauthClient"]["grant_types"]

    # Act
    application = ApplicationJsonConverter.from_dict(payload)

    # Assert
    assert application is not None
    assert application.id == "someid"
    assert application.settings.oauth_client.grant_types is None


def test_user_factor_accepts_fulfillment_errored_status() -> None:
    # Act
    factor = UserFactor.from_dict(WEBAUTHN_FACTOR_WITH_FULFILLMENT_ERRORED_STATUS)

    # Assert
    assert factor is not None
    assert factor.id == "fwf1prereg0Xy3Zq5d7"
    assert factor.status == "FULFILLMENT_ERRORED"


def test_user_factor_preserves_declared_status() -> None:
    # Act
    factor = UserFactor.from_dict(SMS_FACTOR_WITH_ACTIVE_STATUS)

    # Assert
    assert factor is not None
    assert factor.id == "sms1standard0Ab2Cd4"
    assert factor.status == "ACTIVE"
