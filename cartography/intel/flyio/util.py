from typing import Any

import requests


def require_non_empty(value: Any, field_name: str) -> Any:
    if value is None or value == "":
        raise ValueError(f"Fly.io record is missing required non-empty {field_name}.")
    return value


def require_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"Fly.io response is missing required list {field_name}.")
    return value


def get_next_cursor(
    page_info: dict[str, Any],
    previous_cursor: str | None,
    resource_name: str,
) -> str | None:
    if not page_info.get("hasNextPage"):
        return None
    next_cursor = page_info.get("endCursor")
    if not next_cursor or next_cursor == previous_cursor:
        raise ValueError(
            f"Fly.io {resource_name} pagination returned hasNextPage=true "
            "without an advancing endCursor.",
        )
    return next_cursor


def get_json(
    api_session: requests.Session,
    url: str,
    **params: Any,
) -> Any:
    response = api_session.get(url, params=params, timeout=(60, 60))
    response.raise_for_status()
    return response.json()


def post_graphql(
    api_session: requests.Session,
    url: str,
    query: str,
    variables: dict[str, Any],
) -> dict[str, Any]:
    response = api_session.post(
        url,
        json={"query": query, "variables": variables},
        timeout=(60, 60),
    )
    response.raise_for_status()
    result = response.json()
    if result.get("errors"):
        raise ValueError(f"Fly.io GraphQL query failed: {result['errors']}")
    return result["data"]
