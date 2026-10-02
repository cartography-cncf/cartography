import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

import requests

from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.client import ZoomRequestLimitError

logger = logging.getLogger(__name__)
T = TypeVar("T")
R = TypeVar("R")


def optional_call(
    surface: str,
    callback: Callable[[], T],
    unavailable: set[str] | None = None,
) -> T | None:
    """Preserve denied surfaces and cache surface-wide denials for one sync.

    Missing scopes, a sustained rate limit and the configured request limit apply
    to every later read of the surface, so they are not retried within the sync.
    """
    if unavailable is not None and surface in unavailable:
        return None
    try:
        return callback()
    except ZoomRequestLimitError as exc:
        if unavailable is not None:
            unavailable.add(surface)
        logger.warning(
            "Zoom %s skipped: %s. Preserving prior data; raise the Zoom request limits to cover it.",
            surface,
            exc,
        )
        return None
    except requests.HTTPError as exc:
        response = exc.response
        if response is None:
            raise
        if response.status_code == 429:
            if unavailable is not None:
                unavailable.add(surface)
            logger.warning(
                "Zoom %s rate limit persisted after retries (HTTP 429). Preserving prior data.",
                surface,
            )
            return None
        code = None
        missing_scope = False
        if response.status_code == 400:
            try:
                error = response.json()
            except requests.exceptions.JSONDecodeError:
                raise exc
            code = error.get("code")
            message = error.get("message")
            # These codes also cover missing tokens and other authentication
            # failures. Only this scope-specific message establishes a denial.
            missing_scope = (
                code in (4700, 4711)
                and isinstance(message, str)
                and message.startswith("Invalid access token, does not contain ")
                and "scope" in message
            )
        if response.status_code != 403 and not (
            response.status_code == 400 and (code == 200 or missing_scope)
        ):
            raise
        if missing_scope and unavailable is not None:
            unavailable.add(surface)
        logger.warning(
            "Zoom %s unavailable (HTTP %s, code %s); check account tier and read scopes. Preserving prior data.",
            surface,
            response.status_code,
            code,
        )
        return None


def is_zoom_error(exc: requests.HTTPError, status: int, code: int) -> bool:
    """Match one documented endpoint-specific status and Zoom error code."""
    response = exc.response
    if response is None or response.status_code != status:
        return False
    try:
        body = response.json()
    except requests.exceptions.JSONDecodeError:
        return False
    return isinstance(body, dict) and body.get("code") == code


def fetch_many(
    client: ZoomClient,
    items: list[T],
    fetch: Callable[[ZoomClient, T], R],
) -> list[R]:
    """Run fetch per item with at most four sessions sharing the request budgets."""
    if not items:
        return []
    if len(items) == 1:
        return [fetch(client, items[0])]
    logger.info("Fetching %d Zoom records with up to four workers", len(items))

    def fetch_chunk(chunk: list[T]) -> list[R]:
        worker = client.fork()
        with worker.session:
            return [fetch(worker, item) for item in chunk]

    # Contiguous chunks keep results in input order.
    size = (len(items) + 3) // 4
    chunks = [items[i : i + size] for i in range(0, len(items), size)]
    with ThreadPoolExecutor(max_workers=4) as executor:
        return [item for chunk in executor.map(fetch_chunk, chunks) for item in chunk]
