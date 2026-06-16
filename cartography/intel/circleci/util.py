import logging
from datetime import datetime
from typing import Any

import requests

from cartography.util import timeit

logger = logging.getLogger(__name__)

_TIMEOUT = (60, 60)


def parse_iso(value: str | None) -> datetime | None:
    """
    Convert a CircleCI ISO 8601 timestamp (e.g. "2021-09-01T12:00:00Z") to a
    timezone-aware datetime so Neo4j stores a native temporal type. Returns None
    when the field is absent.
    """
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@timeit
def paginated_get(
    api_session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch all items from a paginated CircleCI API v2 endpoint. These endpoints
    return ``{"items": [...], "next_page_token": "..."}`` and accept a
    ``page-token`` query parameter to advance.

    :param api_session: Authenticated requests session (Circle-Token header set).
    :param url: Full URL of the API endpoint.
    :param params: Additional query parameters.
    :return: Combined list of all items across all pages.
    """
    all_items: list[dict[str, Any]] = []
    request_params: dict[str, Any] = dict(params or {})

    while True:
        resp = api_session.get(url, params=request_params, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        all_items.extend(data["items"])

        next_token = data.get("next_page_token")
        if not next_token:
            break
        request_params["page-token"] = next_token

    return all_items
