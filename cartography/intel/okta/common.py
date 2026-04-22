from __future__ import annotations

from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Optional

from okta.pagination import PaginationHelper


def _relax_required_fields(*model_paths: str) -> None:
    """
    Work around okta-sdk-python models that mark API response fields as
    required (StrictStr / StrictBool / StrictInt) even though the Okta API
    frequently omits them on real tenants. A strict model_validate rejects
    the whole list response, so we rewrite the given pydantic models to
    make every required field Optional with a None default.

    This is a pragmatic shim, not a tracked upstream fix. The
    overly-restrictive-validation pattern is a known family of bugs in the
    SDK (see okta/okta-sdk-python#498, #479) that the maintainers declared
    fixed in 3.1.0, yet 3.4.2 still ships strict-required fields on several
    response models. We have not filed a specific issue for
    SamlApplicationSettingsSignOn; if sync breaks on another model, extend
    the list below with the exact dotted path.
    """
    import importlib

    for path in model_paths:
        module_name, _, class_name = path.rpartition(".")
        try:
            model_cls = getattr(importlib.import_module(module_name), class_name)
        except (ImportError, AttributeError):
            continue
        changed = False
        for field_info in model_cls.model_fields.values():
            if field_info.is_required():
                field_info.default = None
                field_info.annotation = Optional[field_info.annotation]
                changed = True
        if changed:
            model_cls.model_rebuild(force=True)


# Loosen Okta SDK 3.4.2 models that declare API-optional fields as required.
# See the _relax_required_fields docstring for context.
_relax_required_fields(
    "okta.models.saml_application_settings_sign_on.SamlApplicationSettingsSignOn",
)


class OktaApiError(RuntimeError):
    """Okta API error that preserves the SDK error_code for callers."""

    def __init__(self, context: str, error: Any) -> None:
        self.context = context
        self.error = error
        self.error_code: str | None = getattr(error, "error_code", None)
        super().__init__(f"Okta API error in {context}: {error}")


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
