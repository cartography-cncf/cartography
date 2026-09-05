from __future__ import annotations

from typing import Any
from typing import Awaitable
from typing import Callable

from okta.models.application import Application
from okta.models.application_json_converter import ApplicationJsonConverter
from okta.models.bookmark_application_settings import BookmarkApplicationSettings
from okta.models.bookmark_application_settings_application import (
    BookmarkApplicationSettingsApplication,
)
from okta.models.open_id_connect_application_settings import (
    OpenIdConnectApplicationSettings,
)
from okta.models.open_id_connect_application_settings_client import (
    OpenIdConnectApplicationSettingsClient,
)
from okta.models.saml_application_settings import SamlApplicationSettings
from okta.models.saml_application_settings_sign_on import SamlApplicationSettingsSignOn
from okta.models.swa_application_settings import SwaApplicationSettings
from okta.models.swa_application_settings_application import (
    SwaApplicationSettingsApplication,
)
from okta.models.user_factor import UserFactor
from okta.models.user_factor_call import UserFactorCall
from okta.models.user_factor_email import UserFactorEmail
from okta.models.user_factor_push import UserFactorPush
from okta.models.user_factor_security_question import UserFactorSecurityQuestion
from okta.models.user_factor_signed_nonce import UserFactorSignedNonce
from okta.models.user_factor_sms import UserFactorSMS
from okta.models.user_factor_token import UserFactorToken
from okta.models.user_factor_token_hardware import UserFactorTokenHardware
from okta.models.user_factor_token_hotp import UserFactorTokenHOTP
from okta.models.user_factor_token_software_totp import UserFactorTokenSoftwareTOTP
from okta.models.user_factor_u2_f import UserFactorU2F
from okta.models.user_factor_web import UserFactorWeb
from okta.models.user_factor_web_authn import UserFactorWebAuthn
from okta.pagination import PaginationHelper

OKTA_RESOURCE_NOT_FOUND_ERROR_CODE = "E0000007"

# UserFactor and every model the factorType discriminator can resolve to. Each
# subclass owns its own copy of the inherited FieldInfo, so all of them must be
# patched individually.
_USER_FACTOR_MODELS = (
    UserFactor,
    UserFactorCall,
    UserFactorEmail,
    UserFactorPush,
    UserFactorSecurityQuestion,
    UserFactorSignedNonce,
    UserFactorSMS,
    UserFactorToken,
    UserFactorTokenHardware,
    UserFactorTokenHOTP,
    UserFactorTokenSoftwareTOTP,
    UserFactorU2F,
    UserFactorWeb,
    UserFactorWebAuthn,
)


def _make_fields_optional(model_cls: type[Any], *field_names: str) -> None:
    for field_name in field_names:
        field_info = model_cls.model_fields.get(field_name)
        if field_info and field_info.is_required():
            field_info.default = None
            field_info.annotation = field_info.annotation | None
    model_cls.model_rebuild(force=True)


def _relax_enum_fields(model_cls: type[Any], *field_names: str) -> None:
    """Retype optional enum fields as plain strings so unknown values are kept."""
    for field_name in field_names:
        field_info = model_cls.model_fields.get(field_name)
        if field_info:
            field_info.annotation = str | None
    model_cls.model_rebuild(force=True)


def _remove_field_validator(model_cls: type[Any], validator_name: str) -> None:
    validators = model_cls.__pydantic_decorators__.field_validators
    validators.pop(validator_name, None)


def _patch_okta_sdk_application_models() -> None:
    """Accept application response shapes returned by Okta but rejected by SDK 3.4.4."""
    _make_fields_optional(
        SamlApplicationSettingsSignOn,
        "allow_multiple_acs_endpoints",
        "assertion_signed",
        "honor_force_authn",
        "request_compressed",
        "response_signed",
    )
    _make_fields_optional(
        SwaApplicationSettingsApplication,
        "button_field",
        "password_field",
        "url",
        "username_field",
    )
    _make_fields_optional(BookmarkApplicationSettingsApplication, "url")
    _make_fields_optional(OpenIdConnectApplicationSettingsClient, "grant_types")
    BookmarkApplicationSettings.model_rebuild(force=True)
    OpenIdConnectApplicationSettings.model_rebuild(force=True)
    SamlApplicationSettings.model_rebuild(force=True)
    SwaApplicationSettings.model_rebuild(force=True)

    application_models = {
        Application,
        *ApplicationJsonConverter.SIGN_ON_MODE_MAPPING.values(),
    }
    for model_cls in application_models:
        _remove_field_validator(model_cls, "features_validate_enum")

    browser_plugin_model = ApplicationJsonConverter.SIGN_ON_MODE_MAPPING[
        "BROWSER_PLUGIN"
    ]
    _remove_field_validator(browser_plugin_model, "name_validate_enum")

    for model_cls in application_models:
        model_cls.model_rebuild(force=True)


def _patch_okta_sdk_user_factor_models() -> None:
    """Accept factor statuses returned by Okta but rejected by SDK 3.4.4."""
    # Okta sets FULFILLMENT_PENDING and FULFILLMENT_ERRORED on WebAuthn
    # preregistration factors, but UserFactorStatus only declares the seven
    # lifecycle values, so a single such factor aborts the whole okta sync.
    for model_cls in _USER_FACTOR_MODELS:
        _relax_enum_fields(model_cls, "status")


# DEPRECATED: Remove this Okta SDK 3.4.4 compatibility shim in v1.0.0 after
# okta/okta-sdk-python#546 and #574 are released upstream.
_patch_okta_sdk_application_models()
_patch_okta_sdk_user_factor_models()


class OktaApiError(RuntimeError):
    """Okta API error that preserves the SDK error_code for callers."""

    def __init__(self, context: str, error: Any) -> None:
        self.context = context
        self.error = error
        self.error_code: str | None = getattr(error, "error_code", None)
        super().__init__(f"Okta API error in {context}: {error}")


def is_resource_not_found_error(error: OktaApiError) -> bool:
    return error.error_code == OKTA_RESOURCE_NOT_FOUND_ERROR_CODE


async def collect_paginated(
    api_method: Callable[..., Awaitable[tuple[Any, Any, Any]]],
    limit: int = 200,
    **kwargs: Any,
) -> list[Any]:
    """
    Collect all items from an Okta SDK v3.x list method, raising on error.

    Okta SDK v3.x list methods return `(data, response, error)` and expose
    pagination via the Link header; the new ApiResponse does not offer
    `has_next()` / `next()` helpers, so callers must iterate cursors manually.
    """
    after = kwargs.pop("after", None)
    items: list[Any] = []
    while True:
        data, response, error = await api_method(limit=limit, after=after, **kwargs)
        if error:
            raise OktaApiError(api_method.__name__, error)
        if data:
            items.extend(data)
        cursor = (
            PaginationHelper.extract_next_cursor(response.headers)
            if response is not None
            else None
        )
        if not cursor:
            break
        after = cursor
    return items


def raise_for_okta_error(error: Any, context: str) -> None:
    """Raise an OktaApiError if the Okta SDK returned an error object."""
    if error:
        raise OktaApiError(context, error)
