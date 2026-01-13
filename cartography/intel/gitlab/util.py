"""
GitLab Intel Module Utilities

Common utilities for GitLab API interactions including retry logic,
rate limit handling, and paginated fetch helpers.
"""

import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_MAX_RETRIES = 5
DEFAULT_RETRY_BACKOFF_BASE = 2
DEFAULT_TIMEOUT = 60
DEFAULT_PER_PAGE = 100


def make_request_with_retry(
    method: str,
    url: str,
    headers: dict[str, str],
    params: dict[str, Any] | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout: int = DEFAULT_TIMEOUT,
) -> requests.Response:
    """
    Make an HTTP request with retry logic and rate limit handling.

    Implements exponential backoff for retries and handles GitLab rate limit responses.
    GitLab returns 429 Too Many Requests when rate limited, with Retry-After header.

    :param method: HTTP method ('GET', 'POST', etc.)
    :param url: Request URL
    :param headers: Request headers
    :param params: Optional query parameters
    :param max_retries: Maximum number of retry attempts (default: 5)
    :param timeout: Request timeout in seconds (default: 60)
    :return: Response object
    :raises requests.exceptions.HTTPError: If request fails after all retries
    """
    retry_count = 0
    last_exception: Exception | None = None

    while retry_count <= max_retries:
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                params=params,
                timeout=timeout,
            )

            # Handle rate limiting (429 Too Many Requests)
            if response.status_code == 429:
                retry_after = _get_retry_after(response)
                if retry_count < max_retries:
                    logger.warning(
                        f"GitLab rate limit hit (429). Sleeping {retry_after}s before retry "
                        f"({retry_count + 1}/{max_retries})"
                    )
                    time.sleep(retry_after)
                    retry_count += 1
                    continue
                else:
                    logger.error(
                        f"GitLab rate limit hit (429) after {max_retries} retries. Failing."
                    )
                    response.raise_for_status()

            # Handle server errors (5xx) with retry
            if response.status_code >= 500:
                if retry_count < max_retries:
                    sleep_time = DEFAULT_RETRY_BACKOFF_BASE**retry_count
                    logger.warning(
                        f"GitLab server error ({response.status_code}). "
                        f"Sleeping {sleep_time}s before retry ({retry_count + 1}/{max_retries})"
                    )
                    time.sleep(sleep_time)
                    retry_count += 1
                    continue
                else:
                    logger.error(
                        f"GitLab server error ({response.status_code}) after {max_retries} retries."
                    )
                    response.raise_for_status()

            # Success or client error (4xx other than 429) - return immediately
            return response

        except requests.exceptions.Timeout as e:
            last_exception = e
            if retry_count < max_retries:
                sleep_time = DEFAULT_RETRY_BACKOFF_BASE**retry_count
                logger.warning(
                    f"GitLab request timeout. Sleeping {sleep_time}s before retry "
                    f"({retry_count + 1}/{max_retries})"
                )
                time.sleep(sleep_time)
                retry_count += 1
            else:
                logger.error(f"GitLab request timeout after {max_retries} retries.")
                raise

        except requests.exceptions.ConnectionError as e:
            last_exception = e
            if retry_count < max_retries:
                sleep_time = DEFAULT_RETRY_BACKOFF_BASE**retry_count
                logger.warning(
                    f"GitLab connection error. Sleeping {sleep_time}s before retry "
                    f"({retry_count + 1}/{max_retries})"
                )
                time.sleep(sleep_time)
                retry_count += 1
            else:
                logger.error(f"GitLab connection error after {max_retries} retries.")
                raise

    # Should not reach here, but raise last exception if we do
    if last_exception:
        raise last_exception
    raise requests.exceptions.RequestException("Request failed after all retries")


def _get_retry_after(response: requests.Response) -> int:
    """
    Extract the Retry-After value from response headers.

    GitLab may return:
    - Retry-After header with seconds to wait
    - RateLimit-Reset header with Unix timestamp

    :param response: The 429 response
    :return: Number of seconds to wait before retrying
    """
    # Try Retry-After header first (standard HTTP)
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        try:
            return int(retry_after)
        except ValueError:
            pass

    # Try GitLab-specific RateLimit-Reset header (Unix timestamp)
    rate_limit_reset = response.headers.get("RateLimit-Reset")
    if rate_limit_reset:
        try:
            reset_time = int(rate_limit_reset)
            current_time = int(time.time())
            wait_time = max(1, reset_time - current_time + 1)
            return min(wait_time, 300)  # Cap at 5 minutes
        except ValueError:
            pass

    # Default to 60 seconds if no header found
    return 60


def check_rate_limit_remaining(response: requests.Response) -> None:
    """
    Check if we're approaching the rate limit and log a warning.

    GitLab includes rate limit headers:
    - RateLimit-Limit: Total requests allowed
    - RateLimit-Remaining: Requests remaining
    - RateLimit-Reset: Unix timestamp when limit resets

    :param response: Response to check headers from
    """
    remaining = response.headers.get("RateLimit-Remaining")
    limit = response.headers.get("RateLimit-Limit")

    if remaining and limit:
        try:
            remaining_int = int(remaining)
            limit_int = int(limit)
            if limit_int > 0 and (remaining_int / limit_int) < 0.1:
                logger.warning(
                    f"GitLab rate limit low: {remaining_int}/{limit_int} requests remaining"
                )
        except ValueError:
            pass


def get_single(
    gitlab_url: str,
    token: str,
    endpoint: str,
) -> dict[str, Any]:
    """
    Fetch a single item from a GitLab API endpoint.

    Handles rate limiting and retries automatically.

    :param gitlab_url: Base GitLab instance URL (e.g., 'https://gitlab.com')
    :param token: GitLab API token
    :param endpoint: API endpoint path (e.g., '/api/v4/groups/123')
    :return: The API response as a dict
    :raises requests.exceptions.HTTPError: If request fails after retries
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    api_url = f"{gitlab_url}{endpoint}"
    response = make_request_with_retry("GET", api_url, headers)
    response.raise_for_status()
    check_rate_limit_remaining(response)

    return response.json()


def get_paginated(
    gitlab_url: str,
    token: str,
    endpoint: str,
    extra_params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch all pages from a GitLab API endpoint.

    Handles pagination, rate limiting, and retries automatically.
    This is the primary utility for fetching lists from GitLab APIs.

    :param gitlab_url: Base GitLab instance URL (e.g., 'https://gitlab.com')
    :param token: GitLab API token
    :param endpoint: API endpoint path (e.g., '/api/v4/groups/123/projects')
    :param extra_params: Additional query parameters to include
    :return: List of all items across all pages
    :raises requests.exceptions.HTTPError: If request fails after retries
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    api_url = f"{gitlab_url}{endpoint}"
    params: dict[str, Any] = {
        "per_page": DEFAULT_PER_PAGE,
        "page": 1,
    }
    if extra_params:
        params.update(extra_params)

    results: list[dict[str, Any]] = []

    while True:
        response = make_request_with_retry("GET", api_url, headers, params)
        response.raise_for_status()
        check_rate_limit_remaining(response)

        page_data = response.json()
        if not page_data:
            break

        results.extend(page_data)

        next_page = response.headers.get("x-next-page")
        if not next_page:
            break

        params["page"] = int(next_page)

    return results
