"""
Utility functions for Spacelift GraphQL API interactions.
"""

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Timeout for API calls: (connection timeout, read timeout) in seconds
_TIMEOUT = (60, 60)


def call_spacelift_api(
    session: requests.Session,
    api_endpoint: str,
    query: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Make a GraphQL query to the Spacelift API.
    """
    logger.debug(f"Making GraphQL request to {api_endpoint}")

    # Prepare the GraphQL request payload
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    # Make the POST request to the GraphQL endpoint
    response = session.post(
        api_endpoint,
        json=payload,
        timeout=_TIMEOUT,
    )

    # Raise an exception for HTTP errors (4xx, 5xx)
    response.raise_for_status()

    # Parse the JSON response
    result = response.json()

    # Check for GraphQL errors in the response
    if "errors" in result:
        error_messages = [error.get("message", "Unknown error") for error in result["errors"]]
        error_string = "; ".join(error_messages)
        raise ValueError(f"GraphQL query failed: {error_string}")

    return result


def fetch_all_paginated(
    session: requests.Session,
    api_endpoint: str,
    query: str,
    resource_path: list[str],
    variables: dict[str, Any] | None = None,
    page_size: int = 50,
) -> list[dict[str, Any]]:
    """
    Fetch all paginated results from a Spacelift GraphQL query.
    """
    logger.info(f"Fetching paginated data from {api_endpoint}")

    all_items: list[dict[str, Any]] = []
    cursor = None
    has_next_page = True

    # Initialize variables if not provided
    if variables is None:
        variables = {}

    page_count = 0

    while has_next_page:
        page_count += 1
        logger.debug(f"Fetching page {page_count} (cursor: {cursor})")

        # Update variables with pagination parameters
        page_variables = {
            **variables,
            "cursor": cursor,
            "pageSize": page_size,
        }

        # Make the GraphQL request
        response = call_spacelift_api(
            session,
            api_endpoint,
            query,
            page_variables,
        )

        # Navigate to the paginated data using the resource_path
        data = response
        for key in resource_path:
            data = data.get(key, {})

        # Extract items from this page
        if isinstance(data, list):
            # Simple list response (no edges/nodes structure)
            items = data
            has_next_page = False  # Simple lists aren't paginated in this way
        elif "edges" in data:
            # Relay-style pagination with edges/nodes
            items = [edge["node"] for edge in data.get("edges", [])]
            page_info = data.get("pageInfo", {})
            has_next_page = page_info.get("hasNextPage", False)
            cursor = page_info.get("endCursor")
        elif "nodes" in data:
            # Direct nodes array (alternate GraphQL pagination style)
            items = data.get("nodes", [])
            page_info = data.get("pageInfo", {})
            has_next_page = page_info.get("hasNextPage", False)
            cursor = page_info.get("endCursor")
        else:
            # No pagination structure found, return what we have
            items = [data] if data else []
            has_next_page = False

        all_items.extend(items)
        logger.debug(f"Page {page_count}: Retrieved {len(items)} items (total so far: {len(all_items)})")

    logger.info(f"Fetched {len(all_items)} total items across {page_count} pages")
    return all_items


def fetch_single_query(
    session: requests.Session,
    api_endpoint: str,
    query: str,
    resource_path: list[str],
    variables: dict[str, Any] | None = None,
) -> dict[str, Any] | list[dict[str, Any]]:
    """
    Fetch a single (non-paginated) query result from Spacelift API.
    """
    logger.debug(f"Fetching single query from {api_endpoint}")

    response = call_spacelift_api(
        session,
        api_endpoint,
        query,
        variables,
    )

    # Navigate to the desired data using the resource_path
    data = response
    for key in resource_path:
        data = data.get(key, {})

    return data
