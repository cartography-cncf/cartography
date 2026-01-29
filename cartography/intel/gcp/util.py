"""
Utility functions for GCP API calls with retry logic.

This module provides helpers to handle transient errors from GCP APIs,
including both network-level errors and HTTP 5xx server errors.
"""

import json
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


def determine_role_type_and_scope(role_name: str) -> tuple[str, str]:
    """
    Determine the role type and scope based on the role name.

    :param role_name: The name of the role (e.g., "roles/editor", "organizations/123/roles/custom").
    :return: A tuple of (role_type, scope).
    """
    if role_name.startswith("roles/"):
        # Predefined or basic roles
        if role_name in ["roles/owner", "roles/editor", "roles/viewer"]:
            return "BASIC", "GLOBAL"
        return "PREDEFINED", "GLOBAL"
    if role_name.startswith("organizations/"):
        return "CUSTOM", "ORGANIZATION"
    if role_name.startswith("projects/"):
        return "CUSTOM", "PROJECT"

    # Unknown format, default to custom project
    return "CUSTOM", "PROJECT"


def is_api_disabled_error(e: HttpError) -> bool:
    """
    Check if an HttpError indicates that a GCP API is not enabled on the project.

    This utility helps modules gracefully skip syncing when an API hasn't been
    enabled, rather than crashing the entire sync. It intentionally does NOT
    match general PERMISSION_DENIED errors (IAM misconfigurations) - those
    should still fail loudly.

    Detection strategy:
    1. Primary: Check error.errors[0].reason for 'accessNotConfigured' or 'SERVICE_DISABLED'
    2. Fallback: Check error.message for standard "API not enabled" patterns

    :param e: The HttpError exception to check
    :return: True if the error indicates API is disabled, False otherwise
    """
    try:
        error_json = json.loads(e.content.decode("utf-8"))
        err = error_json.get("error", {})

        # Primary check: Use the 'reason' field (most reliable indicator)
        # This distinguishes API disabled from IAM permission denied
        errors_list = err.get("errors", [])
        if errors_list:
            reason = errors_list[0].get("reason", "")
            if reason in ("accessNotConfigured", "SERVICE_DISABLED"):
                return True
            # Explicitly reject 'forbidden' and other IAM-related reasons
            if reason in (
                "forbidden",
                "insufficientPermissions",
                "IAM_PERMISSION_DENIED",
            ):
                return False

        # Fallback: Check message patterns for APIs that may use different error formats
        message = err.get("message", "")
        return (
            "API has not been used" in message
            or "is not enabled" in message
            or "it is disabled" in message
        )
    except (ValueError, KeyError, AttributeError) as parse_error:
        logger.debug(
            "Failed to parse HttpError response as JSON: %s. Treating as non-API-disabled error.",
            parse_error,
        )
        return False
