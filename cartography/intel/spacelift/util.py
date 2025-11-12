"""
Utility functions for Spacelift GraphQL API interactions.
"""

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Timeout for API calls: (connection timeout, read timeout) in seconds
_TIMEOUT = (60, 60)

# GraphQL mutation to exchange API key ID and secret for a JWT token
_TOKEN_EXCHANGE_MUTATION = """
mutation GetSpaceliftToken($id: ID!, $secret: String!) {
  apiKeyUser(id: $id, secret: $secret) {
    jwt
  }
}
"""


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


def get_spacelift_token(api_endpoint: str, key_id: str, key_secret: str) -> str:
    """
    Exchange Spacelift API key ID and secret for a JWT bearer token.

    This uses the Spacelift GraphQL API's apiKeyUser mutation to obtain a JWT token
    that can be used for authenticated requests. This is the recommended authentication
    method as it avoids storing long-lived tokens.

    :param api_endpoint: Spacelift GraphQL API endpoint (e.g., https://your-account.app.spacelift.io/graphql)
    :param key_id: Spacelift API key ID (26-character ULID)
    :param key_secret: Spacelift API key secret
    :return: JWT bearer token string
    :raises: requests.exceptions.RequestException if the API request fails
    :raises: ValueError if the response doesn't contain a valid token
    """
    logger.info("Exchanging Spacelift API key for JWT token")

    payload = {
        "query": _TOKEN_EXCHANGE_MUTATION,
        "variables": {
            "id": key_id,
            "secret": key_secret,
        },
    }

    try:
        response = requests.post(
            api_endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=_TIMEOUT,
        )
        response.raise_for_status()

        data: dict[str, Any] = response.json()

        # Check for GraphQL errors
        if "errors" in data:
            error_messages = [
                error.get("message", "Unknown error") for error in data["errors"]
            ]
            error_string = "; ".join(error_messages)
            raise ValueError(f"Token exchange failed: {error_string}")

        # Extract JWT token from response
        jwt = data.get("data", {}).get("apiKeyUser", {}).get("jwt")
        if not jwt:
            raise ValueError("Token exchange response did not contain a JWT token")

        logger.info("Successfully obtained JWT token from Spacelift API")
        return jwt

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to exchange Spacelift API key for token: {e}")
        raise
    except (KeyError, ValueError) as e:
        logger.error(f"Invalid response from Spacelift token exchange: {e}")
        raise
