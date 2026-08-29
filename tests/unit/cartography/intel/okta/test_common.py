from copy import deepcopy
from typing import Any

from okta.models.application_json_converter import ApplicationJsonConverter

import cartography.intel.okta.common  # noqa: F401
from tests.data.okta.application import OIN_BROWSER_PLUGIN_APPLICATION
from tests.data.okta.application import SAML_APPLICATION_WITH_UNKNOWN_FEATURE


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
