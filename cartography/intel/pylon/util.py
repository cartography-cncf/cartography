import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

logger = logging.getLogger(__name__)

# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
TIMEOUT = (60, 60)

US_BASE_URL = "https://api.usepylon.com"
EU_BASE_URL = "https://api.eu.usepylon.com"
EU_TOKEN_PREFIX = "pylon_api_eu_"


def resolve_base_url(api_token: str, base_url: str | None) -> str:
    """Return the Pylon API base URL for a token.

    An explicit base URL wins. Otherwise, the token's prefix selects the region:
    `pylon_api_eu_` tokens belong to the EU region, and every other token,
    including tokens created before Pylon added prefixes, to the US region.
    """
    if base_url:
        return base_url.rstrip("/")
    if api_token.startswith(EU_TOKEN_PREFIX):
        return EU_BASE_URL
    return US_BASE_URL


def build_session(api_token: str) -> requests.Session:
    session = requests.Session()
    # Pylon rate limits each endpoint per organization and answers 429 with a
    # Retry-After header, which urllib3 honors.
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    session.headers.update(
        {
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json",
        },
    )
    return session


def get_object(api_session: requests.Session, url: str) -> dict[str, Any]:
    response = api_session.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()["data"]


def paginated_get(
    api_session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Fetch every page of a Pylon list endpoint.

    Pylon list endpoints return `pagination.has_next_page` and an opaque
    `pagination.cursor` to send back as the `cursor` query parameter. A page
    that claims more results without a new cursor raises an error, so a sync
    never cleans up nodes from an incomplete listing.
    """
    results: list[dict[str, Any]] = []
    seen_cursors: set[str] = set()
    cursor: str | None = None
    while True:
        page_params = dict(params or {})
        if cursor:
            page_params["cursor"] = cursor
        response = api_session.get(url, params=page_params, timeout=TIMEOUT)
        response.raise_for_status()
        body = response.json()
        results.extend(body["data"] or [])
        pagination = body.get("pagination") or {}
        if not pagination.get("has_next_page"):
            return results
        cursor = pagination.get("cursor")
        if not cursor or cursor in seen_cursors:
            raise ValueError(
                f"Pylon returned has_next_page without a new cursor for {url}.",
            )
        seen_cursors.add(cursor)
