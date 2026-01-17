"""
Utility functions for GCP API calls with retry logic.

This module provides helpers to handle transient errors from GCP APIs,
including both network-level errors and HTTP 5xx server errors.
"""

import logging
from typing import Any
from typing import Dict

import backoff
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# GCP API retry configuration
GCP_RETRYABLE_HTTP_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
GCP_API_MAX_RETRIES = 3
GCP_API_BACKOFF_BASE = 2
GCP_API_BACKOFF_MAX = 30

# Number of retries for network-level errors (handled natively by googleapiclient)
GCP_API_NUM_RETRIES = 5


def is_retryable_gcp_http_error(exc: Exception) -> bool:
    """
    Check if the exception is a retryable GCP API error.

    Per Google Cloud documentation (https://cloud.google.com/storage/docs/retry-strategy),
    HTTP 429 (rate limit) and 5xx (server errors) are transient and should be retried
    with exponential backoff.

    :param exc: The exception to check
    :return: True if the exception is a retryable HTTP error, False otherwise
    """
    if not isinstance(exc, HttpError):
        return False
    return exc.resp.status in GCP_RETRYABLE_HTTP_STATUS_CODES


def gcp_api_backoff_handler(details: Dict) -> None:
    """
    Handler that logs retry attempts for GCP API calls.

    :param details: The backoff details dictionary containing wait, tries, and target info
    """
    wait = details.get("wait")
    if isinstance(wait, (int, float)):
        wait_display = f"{wait:0.1f}"
    elif wait is None:
        wait_display = "unknown"
    else:
        wait_display = str(wait)

    tries = details.get("tries")
    tries_display = str(tries) if tries is not None else "unknown"

    target = details.get("target", "<unknown>")
    exc = details.get("exception")
    exc_info = ""
    if exc and isinstance(exc, HttpError):
        exc_info = f" HTTP {exc.resp.status}"

    logger.warning(
        "GCP API retry: backing off %s seconds after %s tries.%s Calling: %s",
        wait_display,
        tries_display,
        exc_info,
        target,
    )


@backoff.on_exception(  # type: ignore[misc]
    backoff.expo,
    HttpError,
    max_tries=GCP_API_MAX_RETRIES,
    giveup=lambda e: not is_retryable_gcp_http_error(e),
    on_backoff=gcp_api_backoff_handler,
    base=GCP_API_BACKOFF_BASE,
    max_value=GCP_API_BACKOFF_MAX,
)
def _gcp_execute(request: Any) -> Any:
    """Internal function that executes a GCP API request with network retry."""
    # num_retries handles network-level errors (connection drops, timeouts, SSL errors)
    # The backoff decorator handles HTTP 5xx and 429 errors
    return request.execute(num_retries=GCP_API_NUM_RETRIES)


def gcp_api_execute_with_retry(request: Any) -> Any:
    """
    Execute a GCP API request with retry on transient errors.

    This function provides two layers of retry:
    1. Network-level errors (connection drops, timeouts, SSL errors) are handled
       natively by googleapiclient via the num_retries parameter.
    2. HTTP 5xx and 429 errors are handled by the backoff decorator with
       exponential backoff.

    Usage:
        Instead of:
            response = request.execute()

        Use:
            response = gcp_api_execute_with_retry(request)

    :param request: A googleapiclient request object (has an execute() method)
    :return: The response from the API call
    :raises HttpError: If the API call fails after all retries or with a non-retryable error
    """
    return _gcp_execute(request)
