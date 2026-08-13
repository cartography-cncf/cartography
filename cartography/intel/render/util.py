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
            # Report only structural info (keys / types) here, never the entry's raw
            # values - some resource_key values (e.g. "secretFile") wrap plaintext
            # secret content, and that must never end up embedded in an exception
            # message that could get logged.
            if not isinstance(entry, dict) or resource_key not in entry:
                shape = (
                    sorted(entry.keys())
                    if isinstance(entry, dict)
                    else type(entry).__name__
                )
                raise ValueError(
                    f"Render API returned a malformed entry for {url}: expected "
                    f"a '{resource_key}' key; got {shape!r}."
                )
            resource = entry[resource_key]
            if not isinstance(resource, dict):
                raise ValueError(
                    f"Render API returned a malformed entry for {url}: expected "
                    f"'{resource_key}' to be an object, got {type(resource).__name__}."
                )
            page.append(resource)
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


def list_plain_array(
    session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Calls a Render list endpoint whose response is a bare array of resource objects,
    not the `{"<resource_key>": {...}, "cursor": ...}` wrapper `list_paginated()`
    handles (e.g. workspace members, registry credentials, disk snapshots).

    Always makes a single, unpaginated GET. These endpoints document `limit`/`cursor`
    params, but - unlike the wrapped endpoints, where cursor is returned as an opaque
    sibling field on every item - no cursor value is present anywhere in a bare-array
    response, and Render's pagination docs are explicit that cursor is not derived
    from a resource's own id. There is no documented way to construct a valid next-page
    cursor here.

    :param limit: Pass an endpoint's documented `limit` query param when it defaults to
        a page smaller than a real account could plausibly have (e.g. registry
        credentials defaults to 20, max 100 - passing 100 here avoids truncating a
        20+-item account on the *default* page size, which is a real risk this
        function had before `limit` existed). If the response still comes back exactly
        `limit` items long, this raises: that's genuinely ambiguous between "the
        account has exactly `limit` items" and "there are more, unreachable with no
        cursor" - and a caller's scoped cleanup would delete every real resource past
        this page if it silently accepted a possibly-truncated page as complete.

    Raises rather than returning an empty list on a malformed response, so a bad or
    unexpected payload shape cannot be mistaken by a caller's scoped cleanup for a real
    empty inventory of this resource type.
    """
    request_params = dict(params or {})
    if limit is not None:
        request_params["limit"] = limit
    response = session.get(url, params=request_params, timeout=(60, 60))
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, list):
        raise ValueError(
            f"Render API returned a non-list response for {url}: {type(body)}."
        )
    for entry in body:
        if not isinstance(entry, dict):
            raise ValueError(
                f"Render API returned a malformed entry for {url}: expected an "
                f"object, got {type(entry).__name__}."
            )
    if limit is not None and len(body) == limit:
        raise ValueError(
            f"Render API returned exactly the requested limit ({limit}) of items for "
            f"{url}. This bare-array endpoint has no documented cursor to fetch "
            f"further pages, so a full page can't be safely treated as the complete "
            f"inventory - refusing to proceed rather than let scoped cleanup delete "
            f"real resources past this page."
        )
    return body
