import logging
from collections.abc import Iterator
from typing import Any

import requests
from requests.adapters import HTTPAdapter

from cartography.client.http import CappedRetry

logger = logging.getLogger(__name__)

SENTRA_DEFAULT_API_URL = "https://app.sentra.io"

_TIMEOUT = (60, 60)
# Sentra recommends 100 rows per page and allows at most 500.
_PAGE_SIZE = 100
_RETRY_STATUSES = (429, 500, 502, 503, 504)

CURRENT_USER_PATH = "/api/core/users/current"
DATA_CLASSES_SEARCH_PATH = "/api/core/classes/search"
DATA_STORES_SEARCH_PATH = "/api/core/data-stores/search"
ALERTS_SEARCH_PATH = "/api/core/alerts/search"


def build_session(api_key: str) -> requests.Session:
    # Sentra asks clients to back off exponentially on 429 and 502-504. The search
    # endpoints are read-only POSTs, so retrying them is safe.
    retry_policy = CappedRetry(
        total=5,
        backoff_factor=1,
        status_forcelist=_RETRY_STATUSES,
        allowed_methods=["GET", "POST"],
        respect_retry_after_header=True,
    )
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry_policy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {
            "X-Sentra-API-Key": api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    return session


def get_current_user(session: requests.Session, api_url: str) -> dict[str, Any]:
    """Return the API key's user, which names the Sentra organization it belongs to."""
    response = session.get(f"{api_url}{CURRENT_USER_PATH}", timeout=_TIMEOUT)
    response.raise_for_status()
    return response.json()


def post_search(
    session: requests.Session,
    api_url: str,
    path: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    response = session.post(f"{api_url}{path}", json=body, timeout=_TIMEOUT)
    response.raise_for_status()
    return response.json()


def iter_search_pages(
    session: requests.Session,
    api_url: str,
    path: str,
    filters: dict[str, Any] | None = None,
    page_size: int = _PAGE_SIZE,
) -> Iterator[list[dict[str, Any]]]:
    """
    Yield every page of a Sentra search endpoint.

    The search endpoints support keyset pagination: `start_from_id` returns the rows
    whose ID sorts after the given ID. Unlike offset pagination, it does not skip or
    repeat rows when rows are added or removed during the sync.
    """
    cursor: str | None = None
    fetched = 0
    while True:
        body: dict[str, Any] = {"limit": page_size, "no_count": True}
        if filters:
            body["filters"] = filters
        if cursor is not None:
            body["start_from_id"] = cursor
        items = post_search(session, api_url, path, body)["items"]
        fetched += len(items)
        yield items

        if len(items) < page_size:
            break
        next_cursor = items[-1]["id"]
        if next_cursor == cursor:
            raise RuntimeError(
                f"Sentra {path} repeated pagination cursor {next_cursor}",
            )
        cursor = next_cursor

    logger.debug("Fetched %d rows from Sentra %s", fetched, path)
