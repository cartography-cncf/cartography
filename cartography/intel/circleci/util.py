import logging
from datetime import datetime
from typing import Any

import requests
from dateutil.parser import isoparse

from cartography.util import timeit

logger = logging.getLogger(__name__)

_TIMEOUT = (60, 60)


def flatten_labels(labels: list[dict[str, Any]] | None) -> list[str]:
    """
    CircleCI deploy labels come back as a list of {key, value} objects. Neo4j
    properties cannot hold lists of maps, so render each as a "key=value" string.
    """
    return [f"{label['key']}={label['value']}" for label in (labels or [])]


def parse_iso(value: str | None) -> datetime | None:
    """
    Convert a CircleCI ISO 8601 / RFC 3339 timestamp (e.g. "2021-09-01T12:00:00Z")
    to a timezone-aware datetime so Neo4j stores a native temporal type. Returns
    None when the field is absent.
    """
    if not value:
        return None
    return isoparse(value)


@timeit
def paginated_get(
    api_session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
    max_pages: int | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch all items from a paginated CircleCI API v2 endpoint. These endpoints
    return ``{"items": [...], "next_page_token": "..."}`` and accept a
    ``page-token`` query parameter to advance.

    :param api_session: Authenticated requests session (Circle-Token header set).
    :param url: Full URL of the API endpoint.
    :param params: Additional query parameters.
    :param max_pages: Stop after this many pages (high-volume endpoints like
        pipelines are effectively unbounded). None means fetch everything.
    :return: Combined list of all items across all pages.
    """
    all_items: list[dict[str, Any]] = []
    request_params: dict[str, Any] = dict(params or {})
    pages = 0

    while True:
        resp = api_session.get(url, params=request_params, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        all_items.extend(data["items"])
        pages += 1

        next_token = data.get("next_page_token")
        if not next_token:
            break
        if max_pages is not None and pages >= max_pages:
            logger.warning(
                "Reached max_pages=%d for %s; stopping pagination early "
                "(some items not ingested).",
                max_pages,
                url,
            )
            break
        request_params["page-token"] = next_token

    return all_items
