import logging
from typing import Any
from typing import Callable

import backoff
import httpx

from cartography.helpers import backoff_handler

logger = logging.getLogger(__name__)

# Transient transport errors that are safe to retry (HTTP/2 resets, connection drops, etc.)
TRANSIENT_EXCEPTIONS = (httpx.ReadError, httpx.ConnectError, httpx.RemoteProtocolError)
MAX_RETRIES = 3


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
