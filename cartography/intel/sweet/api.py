import logging
from typing import Any
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter

from cartography.client.http import CappedRetry

logger = logging.getLogger(__name__)

DEFAULT_API_URL = "https://eapi.sweet.security"
_TIMEOUT = (10, 120)
_PAGE_SIZE = 200
_NEXT_KEYSET_HEADER = "x-sweet-next-keyset"
_RETRY_STATUSES = (429, 500, 502, 503, 504)
_PROGRESS_PAGE_INTERVAL = 10


def normalize_api_url(api_url: str) -> str:
    """Validate a Sweet API origin and return it without a trailing slash."""
    parsed = urlparse(api_url.strip())
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Sweet API URL must be an absolute HTTPS origin")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Sweet API URL must not contain user information")
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError("Sweet API URL contains an invalid port") from exc
    if parsed.path.rstrip("/") or parsed.params or parsed.query or parsed.fragment:
        raise ValueError(
            "Sweet API URL must be an origin without a path, query, or fragment",
        )
    return f"https://{parsed.netloc}"


def create_session() -> requests.Session:
    # Sweet rate-limits with 429. Every call this module makes is either a read or
    # the token exchange, so all of them are safe to repeat.
    retry_policy = CappedRetry(
        total=5,
        read=1,
        backoff_factor=1,
        status_forcelist=_RETRY_STATUSES,
        allowed_methods=frozenset({"GET", "POST"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    session.headers.update(
        {
            "Accept": "application/json",
            "User-Agent": "cartography-sweet",
        },
    )
    return session


def authenticate(
    session: requests.Session,
    api_url: str,
    api_key: str,
    api_secret: str,
) -> None:
    """Exchange the API key and secret for a JWT and attach it to the session."""
    response = session.post(
        f"{api_url}/v1/auth/token",
        json={"apiKey": api_key, "secret": api_secret},
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    access_token = response.json()["accessToken"]
    session.headers["Authorization"] = f"Bearer {access_token}"


def get_list(
    session: requests.Session,
    api_url: str,
    path: str,
) -> list[dict[str, Any]]:
    """Fetch an unpaginated list endpoint."""
    response = session.get(f"{api_url}{path}", timeout=_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise RuntimeError(f"Sweet GET {path} returned a non-list response")
    return payload


def get_paginated(
    session: requests.Session,
    api_url: str,
    path: str,
    params: dict[str, Any],
    label: str,
) -> list[dict[str, Any]]:
    """Fetch every page of a keyset-paginated list endpoint."""
    results: list[dict[str, Any]] = []
    keyset: str | None = None
    seen_keysets: set[str] = set()
    page_count = 0

    while True:
        page_params = {**params, "limit": _PAGE_SIZE}
        if keyset:
            page_params["keyset"] = keyset
        response = session.get(
            f"{api_url}{path}",
            params=page_params,
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        page = response.json()
        if not isinstance(page, list):
            raise RuntimeError(f"Sweet GET {path} returned a non-list response")
        results.extend(page)
        page_count += 1
        if page_count % _PROGRESS_PAGE_INTERVAL == 0:
            logger.info(
                "Fetched %d Sweet %s across %d page(s) so far.",
                len(results),
                label,
                page_count,
            )

        keyset = response.headers.get(_NEXT_KEYSET_HEADER)
        if not keyset:
            break
        if keyset in seen_keysets:
            raise RuntimeError(
                f"Sweet GET {path} repeated pagination keyset {keyset}",
            )
        seen_keysets.add(keyset)

    logger.info("Fetched %d Sweet %s in total.", len(results), label)
    return results
