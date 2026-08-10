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


_PAGE_SIZE = 1000


def list_resources(
    session: requests.Session,
    url: str,
    data_key: str,
    cursor_field: str = "uuid",
) -> list[dict[str, Any]]:
    """
    Calls a Unikraft Cloud "list" endpoint (GET with an empty request body,
    which the API documents as returning every resource of that type) and
    returns every page of the `data[data_key]` payload.

    Pagination follows the documented `count` / `from` cursor params
    (`from` resumes listing after the given `cursor_field` value, sorted by
    create time ascending): a page shorter than `count` is the last page,
    and a `from` cursor that fails to advance would loop forever, so that
    case raises.
    """
    items: list[dict[str, Any]] = []
    previous_cursor: str | None = None
    params: dict[str, Any] = {
        "count": _PAGE_SIZE,
        "order": "PAGINATION_ORDER_ASC",
        "sortby": "PAGINATION_SORT_BY_CREATE_TIME",
    }
    while True:
        response = session.request("GET", url, json=[], params=params, timeout=(60, 60))
        response.raise_for_status()
        body = response.json()
        if body.get("status") == "error":
            raise ValueError(
                f"Unikraft API returned an error for {url}: {body.get('message')}"
            )
        page = (body.get("data") or {}).get(data_key) or []
        items.extend(page)
        if len(page) < _PAGE_SIZE:
            return items
        next_cursor = page[-1].get(cursor_field)
        if not next_cursor or next_cursor == previous_cursor:
            raise ValueError(
                f"Unikraft pagination for {url} returned a full page without an "
                "advancing cursor."
            )
        previous_cursor = next_cursor
        params = {**params, "from": next_cursor}
