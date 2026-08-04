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

# Plan-gated endpoints do not answer 402 or 403 as one would expect. They answer
# HTTP 400 with this error code in the body, e.g. /vanity-subdomain and
# /custom-hostname on a free-tier organization. Matching on the code rather than
# on the bare 400 keeps genuine bad requests loud.
_ENTITLEMENT_ERROR_CODE = "entitlement_required"


def _is_entitlement_error(response: requests.Response) -> bool:
    """
    True when a 400 response is really "your plan does not include this feature".
    """
    if response.status_code != 400:
        return False
    try:
        body = response.json()
    except ValueError:
        return False
    if not isinstance(body, dict):
        return False
    error = body.get("error")
    if not isinstance(error, dict):
        return False
    return error.get("code") == _ENTITLEMENT_ERROR_CODE


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
        ``TOLERATED_STATUSES`` for plan-gated or beta endpoints. When non-empty,
        a 400 carrying the ``entitlement_required`` error code is tolerated too.
    :return: Decoded JSON body, or None when a tolerated status was returned.

    ``None`` means "we could not read this inventory", which callers must treat
    differently from a 200 returning an empty list, which means "this inventory is
    empty". Only the latter may drive a cleanup: see warn_unavailable().
    """
    response = api_session.get(url, timeout=_TIMEOUT)
    if tolerate and (
        response.status_code in tolerate or _is_entitlement_error(response)
    ):
        logger.warning(
            "Supabase returned %d for %s - skipping (feature unavailable on this plan).",
            response.status_code,
            url,
        )
        return None
    response.raise_for_status()
    return response.json()


def warn_unavailable(resource: str, project_ref: str) -> None:
    """
    Log that a resource could not be listed, so its load and cleanup are skipped.

    A tolerated status means "we do not know what exists here", which is not the
    same as a 200 returning an empty list, which means "nothing exists here".
    Treating the two alike would let a plan downgrade, a revoked scope or a
    transient 403 wipe a real inventory of keys, branches, secrets or buckets from
    the graph. So when the read fails we leave the previous nodes alone: stale data
    is recoverable on the next successful sync, deleted data is not.
    """
    logger.warning(
        "Supabase %s for project %s could not be listed - leaving any existing "
        "nodes in place and skipping their cleanup.",
        resource,
        project_ref,
    )


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
