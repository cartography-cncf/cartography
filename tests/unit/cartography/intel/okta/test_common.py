import asyncio
import json
from copy import deepcopy
from types import SimpleNamespace
from typing import Any

import pytest
from okta.models.application_json_converter import ApplicationJsonConverter
from okta.models.authenticator_base import AuthenticatorBase
from okta.models.user_factor import UserFactor

import cartography.intel.okta.common  # noqa: F401
from cartography.intel.okta.common import collect_paginated
from cartography.intel.okta.common import OktaApiError
from tests.data.okta.application import APPLICATION_WITH_REDITECT_URIS
from tests.data.okta.application import BOOKMARK_APPLICATION_WITHOUT_URL
from tests.data.okta.application import OIN_BROWSER_PLUGIN_APPLICATION
from tests.data.okta.application import SAML_APPLICATION_WITH_UNKNOWN_FEATURE
from tests.data.okta.authenticators import TAC_AUTHENTICATOR
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


def test_tac_authenticator_accepts_uppercase_provider_type() -> None:
    # Act
    authenticator = AuthenticatorBase.from_dict(TAC_AUTHENTICATOR)

    # Assert
    assert authenticator is not None
    assert authenticator.provider is not None
    assert authenticator.provider.type == "TAC"


def test_tac_authenticator_preserves_declared_lowercase_provider_type() -> None:
    # Arrange
    payload = deepcopy(TAC_AUTHENTICATOR)
    payload["provider"]["type"] = "tac"

    # Act
    authenticator = AuthenticatorBase.from_dict(payload)

    # Assert
    assert authenticator is not None
    assert authenticator.provider is not None
    assert authenticator.provider.type == "tac"


def _okta_response(next_cursor: str | None) -> SimpleNamespace:
    """Build a response whose Link header mimics the Okta API's cursor paging."""
    links = ['<https://example.okta.com/api/v1/users?limit=200>; rel="self"']
    if next_cursor is not None:
        links.append(
            f"<https://example.okta.com/api/v1/users?after={next_cursor}&limit=200>;"
            ' rel="next"'
        )
    return SimpleNamespace(headers={"link": ", ".join(links)})


def test_collect_paginated_returns_the_final_page() -> None:
    # Arrange
    # The last page carries items but no `next` link, so a reader that stops
    # before collecting it would silently drop the final page of results.
    pages = [
        (["u1", "u2"], _okta_response("CURSOR2"), None),
        (["u3"], _okta_response(None), None),
    ]
    requested_cursors: list[str | None] = []

    async def fake_list(limit: int | None = None, after: str | None = None) -> Any:
        requested_cursors.append(after)
        return pages[len(requested_cursors) - 1]

    # Act
    items = asyncio.run(collect_paginated(fake_list, limit=200))

    # Assert
    assert items == ["u1", "u2", "u3"]
    assert requested_cursors == [None, "CURSOR2"]


def test_collect_paginated_stops_on_a_page_without_a_next_cursor() -> None:
    # Arrange
    calls = 0

    async def fake_list(limit: int | None = None, after: str | None = None) -> Any:
        nonlocal calls
        calls += 1
        return (["only"], _okta_response(None), None)

    # Act
    items = asyncio.run(collect_paginated(fake_list, limit=200))

    # Assert
    assert items == ["only"]
    assert calls == 1


def test_collect_paginated_raises_on_an_api_error() -> None:
    # Arrange
    async def fake_list(limit: int | None = None, after: str | None = None) -> Any:
        return (None, None, SimpleNamespace(error_code="E0000007"))

    # Act and assert
    with pytest.raises(OktaApiError):
        asyncio.run(collect_paginated(fake_list, limit=200))
