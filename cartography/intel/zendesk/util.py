import re
from typing import Any
from urllib.parse import urlsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_RETRY_STATUS_CODES = (408, 429, *range(500, 600))
_RETRY_TOTAL = 4
_RETRY_BACKOFF_FACTOR = 1
_RETRY_BACKOFF_MAX = 16


def configure_session(session: requests.Session) -> None:
    """Configure bounded retries for the shared, read-only Zendesk session."""
    retry_policy = Retry(
        total=_RETRY_TOTAL,
        connect=_RETRY_TOTAL,
        read=_RETRY_TOTAL,
        status=_RETRY_TOTAL,
        other=0,
        allowed_methods=frozenset({"GET"}),
        status_forcelist=_RETRY_STATUS_CODES,
        backoff_factor=_RETRY_BACKOFF_FACTOR,
        backoff_max=_RETRY_BACKOFF_MAX,
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))


def normalize_subdomain(subdomain: str) -> str:
    subdomain = subdomain.strip().lower()
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", subdomain):
        raise ValueError("Zendesk subdomain must be a hostname label, e.g. acme.")
    return subdomain


def get_paginated(
    session: requests.Session,
    subdomain: str,
    endpoint: str,
    key: str,
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    """Fetch a complete cursor-paginated collection before loading or cleanup."""
    base_url = f"https://{subdomain}.zendesk.com"
    url: str | None = f"{base_url}/api/v2/{endpoint}.json"
    query: dict[str, Any] | None = {**params, "page[size]": 100}
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    while url:
        # Never send the bearer credential to a different pagination host.
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != f"{subdomain}.zendesk.com":
            raise ValueError("Zendesk pagination URL must stay on the tenant host.")
        if url in seen:
            raise ValueError("Zendesk returned a repeated pagination URL.")
        seen.add(url)
        response = session.get(
            url, params=query, timeout=(60, 60), allow_redirects=False
        )
        response.raise_for_status()
        page = response.json()
        results.extend(page[key])
        if not page["meta"]["has_more"]:
            break
        links = page.get("links")
        next_url = links.get("next") if isinstance(links, dict) else None
        if not isinstance(next_url, str) or not next_url.strip():
            raise ValueError(
                "Zendesk reports more results without a usable next-page URL."
            )
        url = next_url
        query = None
    return results
