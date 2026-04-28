"""
Utility functions for GCP API calls with retry logic.

This module provides helpers to handle transient errors from GCP APIs,
including both network-level errors and HTTP 5xx server errors.
"""

import json
import logging
from typing import Any
from typing import cast
from typing import Dict
from typing import List

import backoff
from google.api_core.exceptions import ServerError
from google.api_core.exceptions import TooManyRequests
from google.protobuf.json_format import MessageToDict
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# GCP API retry configuration
GCP_RETRYABLE_HTTP_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
GCP_API_MAX_RETRIES = 3
GCP_API_BACKOFF_BASE = 2
GCP_API_BACKOFF_MAX = 30
GCP_HTTP_ERROR_DETAIL_MAX_CHARS = 240
GCP_PERMISSION_DENIED_REASONS = frozenset(
    {"forbidden", "insufficientPermissions", "IAM_PERMISSION_DENIED"}
)
GCP_QUOTA_EXCEEDED_REASONS = frozenset(
    {
        "rateLimitExceeded",  # legacy REST API style
        "userRateLimitExceeded",  # legacy REST API style
        "RATE_LIMIT_EXCEEDED",  # gRPC-transcoded / ErrorInfo style
        "USER_RATE_LIMIT_EXCEEDED",  # gRPC-transcoded / ErrorInfo style
    }
)

# Number of retries for network-level errors (handled natively by googleapiclient)
GCP_API_NUM_RETRIES = 5


def proto_message_to_dict(
    message: object,
    *,
    preserving_proto_field_name: bool = False,
) -> dict[str, Any]:
    proto = getattr(message, "_pb", None)
    if proto is None:
        raise TypeError(f"Expected protobuf-backed message, got {type(message)!r}")
    return cast(
        dict[str, Any],
        MessageToDict(
            proto,
            preserving_proto_field_name=preserving_proto_field_name,
        ),
    )


def is_retryable_gcp_http_error(exc: Exception) -> bool:
    """
    Check if the exception is a retryable GCP API error.

    Per Google Cloud documentation (https://cloud.google.com/storage/docs/retry-strategy),
    HTTP 429 (rate limit) and 5xx (server errors) are transient and should be retried
    with exponential backoff.

    Some older GCP APIs return 403 with reason rateLimitExceeded or userRateLimitExceeded
    instead of 429. These are also retryable.

    :param exc: The exception to check
    :return: True if the exception is a retryable HTTP error, False otherwise
    """
    if isinstance(exc, (ServerError, TooManyRequests)):
        return True
    if not isinstance(exc, HttpError):
        return False
    if exc.resp.status in GCP_RETRYABLE_HTTP_STATUS_CODES:
        return True
    if exc.resp.status == 403:
        return get_error_reason(exc) in GCP_QUOTA_EXCEEDED_REASONS
    return False


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
    elif exc and isinstance(exc, ServerError):
        exc_info = f" HTTP {exc.code}"

    logger.warning(
        "GCP API retry: backing off %s seconds after %s tries.%s Calling: %s",
        wait_display,
        tries_display,
        exc_info,
        target,
    )


def _truncate_gcp_error_detail(
    value: str, limit: int = GCP_HTTP_ERROR_DETAIL_MAX_CHARS
) -> str:
    value = " ".join(value.split())
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def summarize_gcp_http_error(http_error: HttpError) -> str:
    """
    Return a concise, single-line summary for a GCP HttpError.
    """
    status = getattr(http_error.resp, "status", "unknown")
    reason = get_error_reason(http_error)
    prefix = f"HTTP {status}"
    if reason:
        prefix = f"{prefix} {reason}"
    fallback = f"{prefix}: {_truncate_gcp_error_detail(str(http_error))}"

    try:
        data = json.loads(http_error.content.decode("utf-8"))
        if isinstance(data, dict):
            error_obj = data.get("error", {})
            if isinstance(error_obj, dict):
                message = error_obj.get("message")
                if isinstance(message, str) and message:
                    return f"{prefix}: {_truncate_gcp_error_detail(message)}"
    except (UnicodeDecodeError, ValueError, KeyError, IndexError, TypeError):
        return fallback

    return fallback


def gcp_api_giveup_handler(details: Dict) -> None:
    """
    Handler that logs exhausted retries concisely.

    The default backoff logger includes the full HttpError repr, which is
    extremely noisy for non-retryable GCP 403s. Suppress those give-up logs
    entirely and keep retryable exhaustion to a short one-liner.
    """
    tries = details.get("tries")
    tries_display = str(tries) if tries is not None else "unknown"

    target = details.get("target", "<unknown>")
    exc = details.get("exception")
    if exc and isinstance(exc, HttpError):
        if not is_retryable_gcp_http_error(exc):
            return
        logger.warning(
            "GCP API retries exhausted after %s tries. %s Calling: %s",
            tries_display,
            summarize_gcp_http_error(exc),
            target,
        )
        return
    if exc and isinstance(exc, ServerError):
        logger.warning(
            "GCP API retries exhausted after %s tries. HTTP %s: %s Calling: %s",
            tries_display,
            exc.code,
            exc,
            target,
        )
        return

    logger.warning(
        "GCP API retries exhausted after %s tries. Calling: %s",
        tries_display,
        target,
    )


@backoff.on_exception(  # type: ignore[misc]
    backoff.expo,
    (HttpError, ServerError),
    max_tries=GCP_API_MAX_RETRIES,
    giveup=lambda e: not is_retryable_gcp_http_error(e),
    on_backoff=gcp_api_backoff_handler,
    on_giveup=gcp_api_giveup_handler,
    logger=None,
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


def get_error_reason(http_error: HttpError) -> str:
    """
    Extract the `reason` field from a googleapiclient HttpError response body.
    """
    try:
        data = json.loads(http_error.content.decode("utf-8"))
        if isinstance(data, dict):
            error_obj = data.get("error", {})
            if not isinstance(error_obj, dict):
                return ""

            # Standard GCP error shape.
            errors = error_obj.get("errors", [])
            if isinstance(errors, list) and errors:
                first_error = errors[0]
                if isinstance(first_error, dict):
                    reason = first_error.get("reason")
                    if isinstance(reason, str):
                        return reason

            # gRPC-transcoded shape often used by newer APIs:
            # error.details[] with type.googleapis.com/google.rpc.ErrorInfo
            details = error_obj.get("details", [])
            if isinstance(details, list):
                for detail in details:
                    if isinstance(detail, dict):
                        reason = detail.get("reason")
                        if isinstance(reason, str):
                            return reason

                for detail in details:
                    if not isinstance(detail, dict):
                        continue
                    violations = detail.get("violations", [])
                    if isinstance(violations, list):
                        for violation in violations:
                            if isinstance(violation, dict):
                                violation_type = violation.get("type")
                                if isinstance(violation_type, str):
                                    return violation_type

            return ""

        if isinstance(data, list) and data:
            item = data[0]
            if isinstance(item, dict):
                error_obj = item.get("error", {})
                if isinstance(error_obj, dict):
                    errors = error_obj.get("errors", [])
                    if isinstance(errors, list) and errors:
                        first_error = errors[0]
                        if isinstance(first_error, dict):
                            reason = first_error.get("reason")
                            if isinstance(reason, str):
                                return reason

        return ""
    except (UnicodeDecodeError, ValueError, KeyError, IndexError, TypeError):
        logger.warning("HttpError: %s", http_error)
        return ""


def is_billing_disabled_error(e: HttpError) -> bool:
    """
    Check if an HttpError indicates that billing is disabled for the project.
    """
    reason = get_error_reason(e)
    if reason == "BILLING_DISABLED":
        return True
    if reason:
        return False

    try:
        error_json = json.loads(e.content.decode("utf-8"))
        err = error_json.get("error", {}) if isinstance(error_json, dict) else {}
        message = err.get("message", "")
        if isinstance(message, str):
            lowered = message.lower()
            return (
                "requires billing to be enabled" in lowered
                or "billing is disabled for project" in lowered
            )
        return False
    except (ValueError, UnicodeDecodeError, AttributeError):
        return False


def is_permission_denied_error(e: HttpError) -> bool:
    """
    Check if an HttpError indicates an IAM permission denied condition.

    This identifies authorization failures distinct from API-disabled and
    billing-disabled errors.
    """
    return get_error_reason(e) in GCP_PERMISSION_DENIED_REASONS


def parse_compute_full_uri_to_partial_uri(
    full_uri: str | None,
    version: str | None = None,
) -> str | None:
    """
    Convert a Compute API full URI to Cartography's partial URI form.

    If `version` is not provided, auto-detect v1/beta/alpha paths.
    """
    if not full_uri:
        return None
    if full_uri.startswith("projects/"):
        return full_uri

    versions = [version] if version else ["v1", "beta", "alpha"]
    for v in versions:
        marker = f"compute/{v}/"
        _, sep, partial = full_uri.partition(marker)
        if sep:
            return partial

    logger.debug(
        "Unexpected Compute URI format; keeping original value: %s",
        full_uri,
    )
    return full_uri


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


def parse_and_validate_gcp_requested_syncs(gcp_requested_syncs: str) -> List[str]:
    from cartography.intel.gcp.resources import RESOURCE_FUNCTIONS

    validated_resources: List[str] = []
    for resource in gcp_requested_syncs.split(","):
        resource = resource.strip()

        if resource in RESOURCE_FUNCTIONS:
            validated_resources.append(resource)
        else:
            valid_syncs: str = ", ".join(RESOURCE_FUNCTIONS)
            raise ValueError(
                f'Error parsing `gcp-requested-syncs`. You specified "{gcp_requested_syncs}". '
                f"Please check that your string is formatted properly. "
                f'Example valid input looks like "compute,iam,storage" or "compute, gke, cloud_sql". '
                f"Our full list of valid values is: {valid_syncs}.",
            )
    return validated_resources


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
            if reason in GCP_PERMISSION_DENIED_REASONS:
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


def classify_gcp_http_error(e: HttpError) -> str:
    """
    Classify a GCP HttpError into a canonical category string.

    Reuses existing helpers (is_api_disabled_error, get_error_reason, etc.) so
    logic is not duplicated. Malformed or non-JSON bodies never raise; they are
    classified as "unknown".

    Mapping rules:
      - 403 + api-disabled pattern (is_api_disabled_error) → "api_disabled"
      - (other) 403                                        → "forbidden"
      - 404                                                → "not_found"
      - 400 + reason "invalid" or "badRequest"            → "invalid"
      - status in {429, 500, 502, 503, 504}               → "transient"
      - anything else                                      → "unknown"

    :param e: The HttpError exception to classify
    :return: One of "api_disabled", "forbidden", "not_found", "invalid",
             "transient", "unknown"
    """
    try:
        status = int(e.resp.status)
    except (AttributeError, TypeError, ValueError):
        return "unknown"

    if status == 403:
        if is_api_disabled_error(e):
            return "api_disabled"
        if get_error_reason(e) in GCP_QUOTA_EXCEEDED_REASONS:
            return "transient"
        return "forbidden"

    if status == 404:
        return "not_found"

    if status == 400:
        reason = get_error_reason(e)
        if reason.lower() in ("invalid", "badrequest"):
            return "invalid"
        return "unknown"

    if status in GCP_RETRYABLE_HTTP_STATUS_CODES:
        return "transient"

    return "unknown"
