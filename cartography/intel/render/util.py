from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

BASE_URL = "https://api.render.com/v1"

# Render's documented GET rate limit is 400 requests/minute; a single page of any
# list endpoint comfortably fits within that.
_PAGE_LIMIT = 100


def build_session(api_key: str) -> requests.Session:
    session = requests.session()
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    session.headers.update({"Authorization": f"Bearer {api_key}"})
    return session


def require_non_empty(value: Any, field_name: str) -> Any:
    if value is None or value == "":
        raise ValueError(f"Render record is missing required non-empty {field_name}.")
    return value


def list_paginated(
    session: requests.Session,
    url: str,
    resource_key: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Calls a Render "list" endpoint and returns the unwrapped resource objects across
    every page.

    Render's documented list response shape is an array of
    `{"<resource_key>": {...}, "cursor": "..."}` entries. This paginates with the
    documented `limit`/`cursor` query params, continuing while a page comes back full
    (`limit` items) and stopping once a short page confirms the list is exhausted.

    Raises rather than returning an empty list on a malformed response, so a bad or
    unexpected payload shape cannot be mistaken by a caller's scoped cleanup for a real
    empty inventory of this resource type.
    """
    items: list[dict[str, Any]] = []
    request_params: dict[str, Any] = dict(params or {})
    request_params["limit"] = _PAGE_LIMIT
    cursor: str | None = None

    while True:
        page_params = dict(request_params)
        if cursor:
            page_params["cursor"] = cursor
        response = session.get(url, params=page_params, timeout=(60, 60))
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, list):
            raise ValueError(
                f"Render API returned a non-list response for {url}: {type(body)}."
            )

        page: list[dict[str, Any]] = []
        for entry in body:
            if not isinstance(entry, dict) or resource_key not in entry:
                raise ValueError(
                    f"Render API returned a malformed entry for {url}: expected "
                    f"a '{resource_key}' key in {entry!r}."
                )
            page.append(entry[resource_key])
        items.extend(page)

        if len(page) < _PAGE_LIMIT:
            break
        cursor = body[-1].get("cursor")
        if not cursor:
            # A full page with no cursor on its last entry is not evidence the list
            # ended here - every entry observed live carries a cursor regardless of
            # position. Silently stopping would let a malformed or changed response
            # shape masquerade as "inventory ended at exactly _PAGE_LIMIT items",
            # and the caller's subsequent scoped cleanup would then delete every
            # real node past this page.
            raise ValueError(
                f"Render API returned a full page for {url} but the last entry has "
                f"no 'cursor' value; refusing to treat this as the end of the list."
            )

    return items
