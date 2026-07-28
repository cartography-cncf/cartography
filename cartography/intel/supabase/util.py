import logging
from datetime import datetime
from datetime import timezone
from typing import Any

import requests
from dateutil import parser as dateutil_parser
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from cartography.util import timeit

logger = logging.getLogger(__name__)

_TIMEOUT = (60, 60)

# The Management API documents a standard limit of 120 requests per minute, with
# stricter limits on some resource-intensive endpoints. Retry on 429 so a large
# estate does not abort the sync.
_RETRY_STATUS_FORCELIST = [429, 500, 502, 503, 504]

# Statuses that mean "this feature is not available on this project" rather than
# "something is broken": many Management API endpoints are plan-gated (branches,
# custom hostnames, network restrictions, PITR) or still in beta and simply 404.
# Mirrors the documented 403 exception in cartography/intel/vercel/util.py.
TOLERATED_STATUSES = (402, 403, 404)


def build_session(access_token: str) -> requests.Session:
    """
    Build an authenticated Management API session with retries.
    """
    api_session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=_RETRY_STATUS_FORCELIST,
        allowed_methods=["GET"],
    )
    api_session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    api_session.headers.update({"Authorization": f"Bearer {access_token}"})
    return api_session


@timeit
def get_json(
    api_session: requests.Session,
    url: str,
    tolerate: tuple[int, ...] = (),
) -> Any:
    """
    GET a Management API endpoint and return the decoded JSON body.

    :param api_session: Authenticated requests session
    :param url: Full URL of the API endpoint
    :param tolerate: HTTP statuses to treat as "feature unavailable". On one of
        these, log a warning and return None instead of raising. Pass
        ``TOLERATED_STATUSES`` for plan-gated or beta endpoints.
    :return: Decoded JSON body, or None when a tolerated status was returned.
    """
    response = api_session.get(url, timeout=_TIMEOUT)
    if response.status_code in tolerate:
        logger.warning(
            "Supabase returned %d for %s - skipping (feature likely unavailable on this plan).",
            response.status_code,
            url,
        )
        return None
    response.raise_for_status()
    return response.json()


def iso_to_datetime(value: Any) -> datetime | None:
    """
    Parse an ISO-8601 timestamp as the Management API returns it (e.g.
    ``2026-07-28T16:37:25.429581Z``) into a datetime, so Neo4j stores a native
    temporal rather than a string.
    """
    if not value:
        return None
    return dateutil_parser.isoparse(str(value))


def epoch_ms_to_datetime(value: Any) -> datetime | None:
    """
    Convert epoch milliseconds to a datetime.

    The edge functions endpoints are the odd ones out: ``created_at`` and
    ``updated_at`` come back as int64 epoch milliseconds while the rest of the
    Management API uses ISO-8601 strings.
    """
    if value is None:
        return None
    return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)
