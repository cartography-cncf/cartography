import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)
# The API caps `limit` at 500. Ask for the maximum: the account is rate limited to a
# sliding window of requests per minute, so fewer, larger pages is the cheaper shape.
_DEFAULT_PAGE_SIZE = 500


@timeit
def create_huntress_api_session(api_key: str, api_secret: str) -> requests.Session:
    """Build the shared session for the Huntress REST API.

    Huntress uses HTTP basic access authentication with the API key as the user and the
    API secret as the password, so `requests` builds the `Authorization` header itself.
    """
    session = requests.Session()
    session.auth = (api_key, api_secret)
    session.headers.update({"Accept": "application/json"})
    # A single transient blip on any page would otherwise abort the whole Huntress sync.
    # Every call this module makes is an idempotent GET, so bounded retries are safe.
    # 429 is included because the API rate limits on a sliding window.
    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    return session


def _build_uri(base_uri: str, path: str) -> str:
    return f"{base_uri.rstrip('/')}/v1/{path}"


def _extract_items(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    """Pull the collection out of a Huntress list response.

    A body that does not carry the documented collection key must not be mistaken for an
    empty page: the cleanup that follows a sync would then delete every node the resource
    had previously ingested. Raise instead, while still accepting a genuine empty list.
    """
    items = payload.get(key)
    if not isinstance(items, list):
        raise ValueError(
            f"Huntress API returned a body without the expected '{key}' collection; "
            "refusing to treat it as an empty result",
        )
    return items


@timeit
def get_paginated_huntress_items(
    api_session: requests.Session,
    base_uri: str,
    path: str,
    key: str,
    params: dict[str, Any] | None = None,
    page_size: int = _DEFAULT_PAGE_SIZE,
) -> list[dict[str, Any]]:
    """Fetch every page of a Huntress list endpoint.

    Pagination is cursor based: each response carries a `pagination` object, and the
    absence of `next_page_token` marks the last page. The API returns a different
    `pagination` shape when the whole collection fits in one page, so the loop keys off
    the token alone and never off the shape of that object.
    """
    uri = _build_uri(base_uri, path)
    results: list[dict[str, Any]] = []
    page_token: str | None = None
    # A server that echoed the same cursor back would otherwise spin forever.
    seen_tokens: set[str] = set()

    while True:
        query = dict(params or {})
        query["limit"] = page_size
        if page_token is not None:
            query["page_token"] = page_token
        response = api_session.get(uri, params=query, timeout=_TIMEOUT)
        response.raise_for_status()

        payload = response.json()
        results.extend(_extract_items(payload, key))

        pagination = payload.get("pagination") or {}
        page_token = pagination.get("next_page_token")
        if not page_token:
            return results
        if page_token in seen_tokens:
            raise ValueError(
                f"Huntress API repeated page token {page_token!r} while fetching {path}",
            )
        seen_tokens.add(page_token)


@timeit
def get_huntress_item(
    api_session: requests.Session,
    base_uri: str,
    path: str,
    key: str,
) -> dict[str, Any]:
    """Fetch a Huntress singleton endpoint, such as `/v1/account`."""
    response = api_session.get(_build_uri(base_uri, path), timeout=_TIMEOUT)
    response.raise_for_status()

    payload = response.json()
    item = payload.get(key)
    if not isinstance(item, dict):
        raise ValueError(
            f"Huntress API returned a body without the expected '{key}' object",
        )
    return item


def required_id(item: dict[str, Any], item_type: str) -> int:
    """Return the required `id` of a Huntress resource, failing loudly when unusable.

    The id becomes the graph identity, so a null or blank one would reach the ingestion
    `MERGE` as `id: None` and collapse every malformed record onto a single node. Reject
    it at the API boundary instead. Indexing raises `KeyError` when the attribute is
    absent, and the explicit check covers an `id` that is present but not the int64 the
    API documents.
    """
    raw_id = item["id"]
    # `bool` is an `int` subclass, so exclude it explicitly.
    if isinstance(raw_id, bool) or not isinstance(raw_id, int):
        raise ValueError(
            f"Huntress returned a {item_type} whose id is not an integer: {raw_id!r}",
        )
    return raw_id
