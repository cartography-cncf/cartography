import re
from typing import Any
from urllib.parse import urlsplit

import requests


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
        url = page["links"]["next"]
        if not url:
            raise ValueError("Zendesk reports more results without a next-page URL.")
        query = None
    return results
