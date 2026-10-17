import asyncio
import json
from copy import deepcopy
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from okta.errors.http_error import HTTPError
from okta.models.application_json_converter import ApplicationJsonConverter
from okta.models.authenticator_base import AuthenticatorBase
from okta.models.user_factor import UserFactor

import cartography.intel.okta.common  # noqa: F401
from cartography.intel.okta.common import collect_paginated
from cartography.intel.okta.common import collect_raw_paginated
from cartography.intel.okta.common import gather_bounded
from cartography.intel.okta.common import is_missing_scope_error
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


def test_collect_paginated_follows_usable_next_cursor() -> None:
    # Arrange
    async def list_devices(limit: int = 200, after: str | None = None, **kwargs: Any):
        response = MagicMock()
        if after is None:
            response.headers = {
                "Link": (
                    "<https://example.okta.com/api/v1/devices?after=cursor-2>; "
                    'rel="next"'
                )
            }
            return ([{"id": "device-1"}], response, None)
        response.headers = {}
        return ([{"id": "device-2"}], response, None)

    # Act
    items = asyncio.run(collect_paginated(list_devices))

    # Assert
    assert items == [{"id": "device-1"}, {"id": "device-2"}]


def test_collect_paginated_raises_on_unusable_next_cursor() -> None:
    # Arrange
    async def list_devices(limit: int = 200, after: str | None = None, **kwargs: Any):
        response = MagicMock()
        response.headers = {
            "Link": '<https://example.okta.com/api/v1/devices?limit=200>; rel="next"'
        }
        return ([{"id": "device-1"}], response, None)

    # Act and assert
    with pytest.raises(OktaApiError, match="unusable cursor"):
        asyncio.run(collect_paginated(list_devices))


class _FakeRequestExecutor:
    def __init__(self, pages: dict[str, tuple[Any, str | None]]) -> None:
        self.pages = pages
        self.urls: list[str] = []

    async def create_request(self, method, url, body, headers):
        return {"method": method, "url": url}, None

    async def execute(self, request):
        self.urls.append(request["url"])
        body, error = self.pages[request["url"]]
        next_url = {
            "/api/v1/policies?type=PASSWORD": "https://example.okta.com/api/v1/policies?type=PASSWORD&after=p2",
        }.get(request["url"])
        response = MagicMock()
        response.links = {"next": {"url": next_url}} if next_url else {}
        return response, json.dumps(body) if body is not None else None, error


def test_collect_raw_paginated_follows_next_links() -> None:
    # Arrange
    executor = _FakeRequestExecutor(
        {
            "/api/v1/policies?type=PASSWORD": ([{"id": "p1"}], None),
            "https://example.okta.com/api/v1/policies?type=PASSWORD&after=p2": (
                [{"id": "p2"}],
                None,
            ),
        },
    )
    okta_client = MagicMock()
    okta_client.get_request_executor.return_value = executor

    # Act
    items = asyncio.run(
        collect_raw_paginated(okta_client, "/api/v1/policies", {"type": "PASSWORD"}),
    )

    # Assert
    assert items == [{"id": "p1"}, {"id": "p2"}]
    assert len(executor.urls) == 2


def test_collect_raw_paginated_raises_okta_api_error() -> None:
    # Arrange
    error = MagicMock(error_code="E0000006")
    executor = _FakeRequestExecutor({"/api/v1/zones": (None, error)})
    okta_client = MagicMock()
    okta_client.get_request_executor.return_value = executor

    # Act / Assert
    with pytest.raises(OktaApiError) as exc_info:
        asyncio.run(collect_raw_paginated(okta_client, "/api/v1/zones"))
    assert exc_info.value.error_code == "E0000006"


def test_gather_bounded_limits_concurrency_and_keeps_order() -> None:
    # Arrange
    running = 0
    peak = 0

    async def double(item: int) -> int:
        nonlocal running, peak
        running += 1
        peak = max(peak, running)
        # Finish later items first, so input order must be restored.
        await asyncio.sleep(0.01 * (5 - item))
        running -= 1
        return item * 2

    # Act
    results = asyncio.run(gather_bounded(double, range(5), limit=2))

    # Assert
    assert results == [0, 2, 4, 6, 8]
    assert peak == 2


def _http_error(status: int, www_authenticate: str | None = None) -> HTTPError:
    headers = {"WWW-Authenticate": www_authenticate} if www_authenticate else {}
    return HTTPError(
        "https://example.okta.com/api/v1/apps/0oaWeb/grants",
        SimpleNamespace(status=status, headers=headers),
        "",
    )


# Okta answers a token without the endpoint's scope with a bare 403.
_INSUFFICIENT_SCOPE = (
    'DPoP realm="https://example.okta.com", scope="okta.appGrants.read", '
    'error="insufficient_scope", '
    'error_description="The access token provided does not contain the required scopes."'
)


@pytest.mark.parametrize(
    ("error", "missing_scope"),
    [
        (SimpleNamespace(error_code="E0000006"), True),
        (_http_error(403, _INSUFFICIENT_SCOPE), True),
        (_http_error(403), False),
        (_http_error(401, 'DPoP error="invalid_token"'), False),
        (SimpleNamespace(error_code="E0000007"), False),
    ],
    ids=["admin-role", "token-scope", "bare-403", "invalid-token", "not-found"],
)
def test_is_missing_scope_error(error, missing_scope):
    # Act and assert
    assert is_missing_scope_error(OktaApiError("request", error)) is missing_scope
