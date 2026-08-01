import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

_TIMEOUT = (60, 60)
_DEFAULT_PAGE_SIZE = 100
WIZ_AUTH_AUDIENCE = "wiz-api"


def get_access_token(
    session: requests.Session,
    auth_url: str,
    client_id: str,
    client_secret: str,
) -> str:
    response = session.post(
        auth_url,
        data={
            "grant_type": "client_credentials",
            "audience": WIZ_AUTH_AUDIENCE,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def graphql_query(
    session: requests.Session,
    graphql_url: str,
    token: str,
    query: str,
    variables: dict[str, Any],
) -> dict[str, Any]:
    response = session.post(
        graphql_url,
        json={"query": query, "variables": variables},
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    errors = payload.get("errors")
    if errors:
        raise RuntimeError(f"Wiz GraphQL query failed: {errors}")
    return payload["data"]


def get_paginated(
    session: requests.Session,
    graphql_url: str,
    token: str,
    query: str,
    connection_name: str,
    filter_by: dict[str, Any] | None = None,
    order_by: dict[str, Any] | None = None,
    page_size: int = _DEFAULT_PAGE_SIZE,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    after = None

    while True:
        variables: dict[str, Any] = {
            "first": page_size,
            "after": after,
        }
        if filter_by is not None:
            variables["filterBy"] = filter_by
        if order_by is not None:
            variables["orderBy"] = order_by
        data = graphql_query(session, graphql_url, token, query, variables)
        connection = data[connection_name]
        nodes = connection.get("nodes") or []
        results.extend(nodes)

        page_info = connection.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        after = page_info.get("endCursor")
        if not after:
            logger.warning(
                "Wiz %s response set hasNextPage but omitted endCursor; stopping pagination",
                connection_name,
            )
            break

    return results
