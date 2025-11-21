import logging
from typing import Any

import requests

from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each
_TIMEOUT = (60, 60)


@timeit
def call_sentinelone_api(
    api_url: str,
    endpoint: str,
    api_token: str,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Call the SentinelOne API
    :param api_url: The base URL for the SentinelOne API
    :param endpoint: The API endpoint to call
    :param api_token: The API token for authentication
    :param method: The HTTP method to use (default is GET)
    :param params: Query parameters to include in the request
    :param data: Data to include in the request body for POST/PUT methods
    :return: The JSON response from the API
    """
    full_url = f"{api_url.rstrip('/')}/{endpoint.lstrip('/')}"

    headers = {
        "Accept": "application/json",
        "Authorization": f"ApiToken {api_token}",
        "Content-Type": "application/json",
    }

    try:
        logger.debug(
            "SentinelOne: %s %s",
            method,
            full_url,
        )

        response = requests.request(
            method=method,
            url=full_url,
            headers=headers,
            params=params,
            json=data,
            timeout=_TIMEOUT,
        )

        # Raise an exception for HTTP errors
        response.raise_for_status()

    except requests.exceptions.Timeout:
        logger.warning(f"SentinelOne: Request to '{full_url}' timed out.")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"SentinelOne API request failed: {e}")
        raise

    return response.json()


def get_paginated_results(
    api_url: str,
    endpoint: str,
    api_token: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Handle cursor-based pagination for SentinelOne API requests
    :param api_url: The base URL for the SentinelOne API
    :param endpoint: The API endpoint to call
    :param api_token: The API token for authentication
    :param params: Query parameters to include in the request
    :return: A list of all items from all pages
    """
    query_params = params or {}

    # Set default pagination parameters if not provided
    if "limit" not in query_params:
        query_params["limit"] = 100

    next_cursor = None
    total_items = []

    while True:
        if next_cursor:
            query_params["cursor"] = next_cursor

        response = call_sentinelone_api(
            api_url=api_url,
            endpoint=endpoint,
            api_token=api_token,
            params=query_params,
        )

        items = response.get("data", [])
        if not items:
            break

        total_items.extend(items)
        pagination = response.get("pagination", {})
        next_cursor = pagination.get("nextCursor")
        if not next_cursor:
            break

    return total_items
