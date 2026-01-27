import logging
from typing import Any

import requests

from cartography.intel.pagination import get_pagination_limits
from cartography.util import backoff_handler
from cartography.util import retries_with_backoff

# Connect and read timeouts of 60 seconds each
_TIMEOUT = (60, 60)
logger = logging.getLogger(__name__)
MAX_PAGINATION_PAGES, MAX_PAGINATION_ITEMS = get_pagination_limits(logger)


def _call_sentinelone_api_base(
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

    response = requests.request(
        method=method,
        url=full_url,
        headers=headers,
        params=params,
        json=data,
        timeout=_TIMEOUT,
    )

    # Raise an exception for HTTP errors (this will be caught by backoff wrapper)
    response.raise_for_status()

    return response.json()


def call_sentinelone_api(
    api_url: str,
    endpoint: str,
    api_token: str,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Call the SentinelOne API with backoff functionality
    :param api_url: The base URL for the SentinelOne API
    :param endpoint: The API endpoint to call
    :param api_token: The API token for authentication
    :param method: The HTTP method to use (default is GET)
    :param params: Query parameters to include in the request
    :param data: Data to include in the request body for POST/PUT methods
    :return: The JSON response from the API
    """
    wrapped_func = retries_with_backoff(
        func=_call_sentinelone_api_base,
        exception_type=requests.exceptions.RequestException,  # Covers Timeout and HTTPError as subclasses
        max_tries=5,  # Maximum number of retry attempts
        on_backoff=backoff_handler,
    )
    return wrapped_func(api_url, endpoint, api_token, method, params, data)


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
    total_items: list[dict[str, Any]] = []
    page_count = 0

    while True:
        if page_count >= MAX_PAGINATION_PAGES:
            logger.warning(
                "SentinelOne: reached max pagination pages (%d). Stopping with %d items.",
                MAX_PAGINATION_PAGES,
                len(total_items),
            )
            break
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
        page_count += 1
        if len(total_items) > MAX_PAGINATION_ITEMS:
            logger.warning(
                "SentinelOne: reached max pagination items (%d). Stopping after %d pages.",
                MAX_PAGINATION_ITEMS,
                page_count,
            )
            break
        pagination = response.get("pagination", {})
        next_cursor = pagination.get("nextCursor")
        if not next_cursor:
            break

    return total_items
