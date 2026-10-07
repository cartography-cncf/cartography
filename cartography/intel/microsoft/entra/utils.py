import logging
from typing import Any
from typing import AsyncGenerator
from typing import Awaitable
from typing import Callable

import backoff
import httpx
from kiota_abstractions.api_error import APIError

from cartography.helpers import backoff_handler

logger = logging.getLogger(__name__)

# Transient transport errors that are safe to retry (HTTP/2 resets, connection drops, etc.)
TRANSIENT_EXCEPTIONS = (httpx.ReadError, httpx.ConnectError, httpx.RemoteProtocolError)
MAX_RETRIES = 3
DIRECTORY_EXPIRED_PAGE_TOKEN = "Directory_ExpiredPageToken"
MAX_EXPIRED_PAGE_TOKEN_RESTARTS = 5


async def call_with_retries(
    func: Callable,
    *args: Any,
    exception_types: tuple[type[Exception], ...] = TRANSIENT_EXCEPTIONS,
    max_tries: int = MAX_RETRIES,
) -> Any:
    """
    Call an async function with retries on transient transport exceptions.

    Uses exponential backoff (1s, 2s, 4s, ...) between retries.
    Non-matching exceptions propagate immediately.

    Args:
        func: The async function to call.
        *args: Positional arguments passed to func.
        exception_types: Tuple of exception classes that trigger retries.
        max_tries: Maximum number of attempts (including the first).
    """

    @backoff.on_exception(  # type: ignore[misc]
        backoff.expo,
        exception_types,
        max_tries=max_tries,
        on_backoff=backoff_handler,
    )
    async def _inner() -> Any:
        return await func(*args)

    return await _inner()


def is_directory_expired_page_token_error(error: Exception) -> bool:
    """
    Return whether a Microsoft Graph error is an expired pagination token.

    Microsoft Graph returns this as a 400 ODataError. Other 400s, including
    authorization/configuration problems expressed through Graph, must continue
    to fail fast.
    """
    if not isinstance(error, APIError):
        return False
    if error.response_status_code != 400:
        return False

    graph_error = error.error
    if graph_error is None:
        return False
    return graph_error.code == DIRECTORY_EXPIRED_PAGE_TOKEN


async def iter_paginated_values_with_expired_page_retry(
    first_page_getter: Callable[[], Awaitable[Any]],
    next_page_getter: Callable[[str], Awaitable[Any]],
    resource_description: str,
    max_expired_page_token_restarts: int = MAX_EXPIRED_PAGE_TOKEN_RESTARTS,
    on_restart: Callable[[], None] | None = None,
) -> AsyncGenerator[list[Any], None]:
    """
    Yield the values of each page of a Microsoft Graph paginated request.

    Only one page is held at a time, so memory stays bounded however large the
    collection is.

    If a next-link fails with Directory_ExpiredPageToken, restart the whole
    request from the first page. Retrying the same expired next-link cannot
    succeed. A restart re-yields pages the caller has already seen, so callers
    must either tolerate duplicates (idempotent loads) or discard what they have
    accumulated in ``on_restart``.
    """
    restart_count = 0

    while True:
        try:
            page = await call_with_retries(first_page_getter)

            while page:
                if page.value:
                    yield page.value

                next_link = page.odata_next_link
                if not next_link:
                    return

                page = await call_with_retries(lambda: next_page_getter(next_link))
            return
        except APIError as e:
            if (
                is_directory_expired_page_token_error(e)
                and restart_count < max_expired_page_token_restarts
            ):
                restart_count += 1
                logger.warning(
                    "Microsoft Graph pagination token expired for %s; "
                    "restarting paginated request from the first page "
                    "(restart %d/%d).",
                    resource_description,
                    restart_count,
                    max_expired_page_token_restarts,
                )
                if on_restart is not None:
                    on_restart()
                continue
            raise


async def get_paginated_values_with_expired_page_retry(
    first_page_getter: Callable[[], Awaitable[Any]],
    next_page_getter: Callable[[str], Awaitable[Any]],
    resource_description: str,
    max_expired_page_token_restarts: int = MAX_EXPIRED_PAGE_TOKEN_RESTARTS,
) -> list[Any]:
    """
    Fetch all values from a Microsoft Graph paginated request.

    Partial results are discarded when an expired page token forces a restart.
    """
    values: list[Any] = []
    async for page_values in iter_paginated_values_with_expired_page_retry(
        first_page_getter,
        next_page_getter,
        resource_description,
        max_expired_page_token_restarts,
        on_restart=values.clear,
    ):
        values.extend(page_values)
    return values
