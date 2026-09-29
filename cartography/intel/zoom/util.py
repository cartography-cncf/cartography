import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from typing import TypeVar
from urllib.parse import quote

import requests

from cartography.intel.zoom.client import ZoomClient

logger = logging.getLogger(__name__)
T = TypeVar("T")


def optional_call(surface: str, callback: Callable[[], T]) -> T | None:
    """Preserve unreadable optional surfaces; credential and server failures raise."""
    try:
        return callback()
    except requests.HTTPError as exc:
        response = exc.response
        if response is None:
            raise
        code = None
        if response.status_code == 400:
            try:
                code = response.json().get("code")
            except requests.exceptions.JSONDecodeError:
                raise exc
        if response.status_code != 403 and not (
            response.status_code == 400 and code in (200, 4700, 4711)
        ):
            raise
        logger.warning(
            "Zoom %s unavailable (HTTP %s, code %s); check account tier and read scopes. Preserving prior data.",
            surface,
            response.status_code,
            code,
        )
        return None


def fetch_many(
    client: ZoomClient, paths: list[str], params: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """Fetch details with at most four independent sessions and a shared budget."""
    if not paths:
        return []
    logger.info("Fetching %d Zoom detail records with up to four workers", len(paths))

    def fetch_chunk(chunk: list[str]) -> list[dict[str, Any]]:
        worker = client.fork()
        with worker.session:
            return [worker.get(path, params) for path in chunk]

    # Contiguous chunks keep response order identical to the input paths.
    size = (len(paths) + 3) // 4
    chunks = [paths[i : i + size] for i in range(0, len(paths), size)]
    with ThreadPoolExecutor(max_workers=4) as executor:
        return [item for chunk in executor.map(fetch_chunk, chunks) for item in chunk]


def date_windows(days: int) -> list[dict[str, str]]:
    """UTC lookback windows, split at calendar months to satisfy report APIs."""
    if not 1 <= days <= 30:
        raise ValueError("Zoom lookback days must be between 1 and 30")
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days - 1)
    windows = []
    while start <= end:
        next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        window_end = min(end, next_month - timedelta(days=1))
        windows.append({"from": start.isoformat(), "to": window_end.isoformat()})
        start = window_end + timedelta(days=1)
    return windows


def parse_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    try:
        timestamp = datetime.fromisoformat(value)
        return timestamp.replace(tzinfo=timestamp.tzinfo or timezone.utc)
    except (ValueError, TypeError):
        logger.warning("Ignoring malformed optional Zoom timestamp")
        return None


def encode_uuid(uuid: str) -> str:
    # Zoom requires a second encoding for UUIDs starting with / or containing //.
    encoded = quote(uuid, safe="")
    return quote(encoded, safe="") if uuid.startswith("/") or "//" in uuid else encoded
