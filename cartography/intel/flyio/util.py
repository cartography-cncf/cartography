from typing import Any

import requests


def require_non_empty(value: Any, field_name: str) -> Any:
    if value is None or value == "":
        raise ValueError(f"Fly.io record is missing required non-empty {field_name}.")
    return value


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
