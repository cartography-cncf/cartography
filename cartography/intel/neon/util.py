import logging
from datetime import datetime
from typing import Any

import requests
from dateutil import parser as dateutil_parser
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from cartography.util import timeit

logger = logging.getLogger(__name__)

_TIMEOUT = (60, 60)

# The Neon API rate-limits requests per account. Retry on 429 (honouring
# Retry-After) so a large estate does not abort the sync.
_RETRY_STATUS_FORCELIST = [429, 500, 502, 503, 504]

# Statuses that mean "this inventory is not readable with this key or on this
# plan", not "something is broken". Object storage and credentials are
# Beta endpoints, and organization-scoped listings answer 403 to a project-scoped
# API key.
TOLERATED_STATUSES = (402, 403, 404)


def build_session(api_key: str) -> requests.Session:
    """
    Build an authenticated Neon API session with retries.
    """
    api_session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=_RETRY_STATUS_FORCELIST,
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )
    api_session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    api_session.headers.update(
        {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
    )
    return api_session


@timeit
def get_json(
    api_session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
    tolerate: tuple[int, ...] = (),
) -> Any:
    """
    GET a Neon API endpoint and return the decoded JSON body.

    :param api_session: Authenticated requests session
    :param url: Full URL of the API endpoint
    :param params: Optional query string parameters
    :param tolerate: HTTP statuses to treat as "inventory unavailable". On one of
        these, log a warning and return None instead of raising.
    :return: Decoded JSON body, or None when a tolerated status was returned.

    ``None`` means "we could not read this inventory", which callers must treat
    differently from a 200 returning an empty list, which means "this inventory is
    empty". Only the latter may drive a cleanup: see warn_unavailable().
    """
    response = api_session.get(url, params=params, timeout=_TIMEOUT)
    if tolerate and response.status_code in tolerate:
        logger.warning(
            "Neon returned %d for %s - skipping (not readable with this key or plan).",
            response.status_code,
            url,
        )
        return None
    response.raise_for_status()
    return response.json()


def get_paginated(
    api_session: requests.Session,
    url: str,
    items_key: str,
    page_size: int,
    params: dict[str, Any] | None = None,
    tolerate: tuple[int, ...] = (),
) -> list[dict[str, Any]] | None:
    """
    Follow a cursor-paginated Neon listing to the end.

    Used for the listings that return ``pagination.next`` (branches,
    organization members). The cursor is followed until the API stops returning
    one or a page comes back empty. It does not stop on a short page, because a
    page shorter than ``limit`` does not promise it is the last. A truncated
    listing would make the missing items look deleted to the cleanup jobs.

    Returns None when the first page answers a tolerated status.
    """
    items: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        page_params = {**(params or {}), "limit": page_size}
        if cursor:
            page_params["cursor"] = cursor
        page = get_json(api_session, url, params=page_params, tolerate=tolerate)
        if page is None:
            if cursor:
                # A later page failing must not pass off a truncated listing as
                # complete.
                raise RuntimeError(f"Neon listing {url} failed mid-pagination")
            return None
        batch = page.get(items_key) or []
        items.extend(batch)
        next_cursor = (page.get("pagination") or {}).get("next")
        if not batch or not next_cursor or next_cursor == cursor:
            return items
        cursor = next_cursor


def warn_unavailable(resource: str, scope: str) -> None:
    """
    Log that a resource could not be listed, so its cleanup is skipped.

    A tolerated status means "we do not know what exists here", which is not the
    same as a 200 returning an empty list, which means "nothing exists here".
    Treating the two alike would let a key with narrower scope, a plan change or
    a transient 403 wipe a real inventory of buckets, credentials or members from
    the graph. Stale data is recoverable on the next successful sync, deleted
    data is not.
    """
    logger.warning(
        "Neon %s for %s could not be listed - leaving any existing nodes in place "
        "and skipping their cleanup.",
        resource,
        scope,
    )


def iso_to_datetime(value: Any) -> datetime | None:
    """
    Parse an ISO-8601 timestamp as the Neon API returns it (e.g.
    ``2026-11-05T10:25:24Z``) into a datetime, so Neo4j stores a native temporal
    instead of a string.
    """
    if not value:
        return None
    return dateutil_parser.isoparse(str(value))
