from __future__ import annotations

from typing import Any
from typing import Awaitable
from typing import Callable

from okta.pagination import PaginationHelper


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
