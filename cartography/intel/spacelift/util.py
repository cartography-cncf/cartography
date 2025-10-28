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
    payload: dict[str, Any] = {"query": query}
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
        error_messages = [
            error.get("message", "Unknown error") for error in result["errors"]
        ]
        error_string = "; ".join(error_messages)
        raise ValueError(f"GraphQL query failed: {error_string}")

    return result
