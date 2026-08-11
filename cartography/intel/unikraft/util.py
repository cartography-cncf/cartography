from typing import Any

import requests

# Unikraft Cloud has no dynamic "list metros" API; the platform's five metros
# are hardcoded here per https://docs.unikraft.com/api/platform/v1/node.
METRO_BASE_URLS: dict[str, str] = {
    "fra": "https://api.fra.unikraft.cloud",
    "dal": "https://api.dal.unikraft.cloud",
    "sin": "https://api.sin.unikraft.cloud",
    "was": "https://api.was.unikraft.cloud",
    "sfo": "https://api.sfo.unikraft.cloud",
}


def require_non_empty(value: Any, field_name: str) -> Any:
    if value is None or value == "":
        raise ValueError(f"Unikraft record is missing required non-empty {field_name}.")
    return value


def list_resources(
    session: requests.Session,
    url: str,
    data_key: str,
) -> list[dict[str, Any]]:
    """
    Calls a Unikraft Cloud "list" endpoint and returns the `data[data_key]`
    payload.

    The platform API docs describe `count`/`from`/`order`/`sortby` query
    params for cursor-based pagination, but every combination of them (as
    query params, as a JSON body, in either casing) is rejected with a 400
    against the live API, confirmed directly. A bare, unparameterized GET is
    the only request shape that actually works, so that is what this sends;
    there is currently no working way to page through results beyond
    whatever a single call returns.
    """
    response = session.get(url, timeout=(60, 60))
    response.raise_for_status()
    body = response.json()
    if body.get("status") == "error":
        raise ValueError(
            f"Unikraft API returned an error for {url}: {body.get('message')}"
        )
    data = body.get("data")
    items = data.get(data_key) if isinstance(data, dict) else None
    if not isinstance(items, list):
        # A real empty result is `{"data": {data_key: []}}`, which is a list.
        # Anything else under a "success" status is a malformed/unexpected
        # payload shape, not evidence the account has zero resources of this
        # type -- treating it as an empty list here would make the caller's
        # subsequent scoped cleanup delete every real node of this type.
        raise ValueError(
            f"Unikraft API returned a success status for {url} but no valid "
            f"'{data_key}' list in the response body."
        )
    return items
