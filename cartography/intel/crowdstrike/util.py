import logging
import time
from typing import Any
from typing import Callable

from falconpy.oauth2 import OAuth2

logger = logging.getLogger(__name__)

# falconpy reports a request timeout as HTTP 500, so this also covers stalled calls.
RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
REQUEST_TIMEOUT_SECONDS = 120


class CrowdstrikeAPIError(RuntimeError):
    pass


def get_authorization(client_id: str, client_secret: str, api_url: str) -> OAuth2:
    authorization = OAuth2(
        creds={"client_id": client_id, "client_secret": client_secret},
        base_url=api_url,
    )
    return authorization


def get_response_body(response: dict[str, Any], operation: str) -> dict[str, Any]:
    """
    Return the body of a falconpy response, raising if the call failed.

    falconpy returns a failed call as an ordinary response whose `resources` list
    is empty. Reading that as the end of the results lets a rate-limited or failed
    page truncate the sync, and the cleanup that follows then deletes everything
    the truncated sync did not see.
    """
    status_code = response.get("status_code")
    body = response.get("body")
    if status_code is None or not 200 <= status_code < 300:
        messages = [error.get("message") for error in (body or {}).get("errors") or []]
        raise CrowdstrikeAPIError(
            f"CrowdStrike {operation} failed with HTTP {status_code}: {messages}",
        )
    if not body:
        raise CrowdstrikeAPIError(
            f"CrowdStrike {operation} returned HTTP {status_code} with no body",
        )
    return body


def call_with_retries(
    call: Callable[[], dict[str, Any]],
    operation: str,
    attempts: int = 4,
    backoff_seconds: float = 5.0,
) -> dict[str, Any]:
    """
    Call a falconpy method and return its body, retrying throttled or failed calls.

    A large tenant's sync makes thousands of calls over many hours, so a single
    transient failure would otherwise abort the whole run before cleanup.
    """
    for attempt in range(1, attempts):
        response = call()
        status_code = response.get("status_code")
        if status_code not in RETRYABLE_STATUS_CODES:
            return get_response_body(response, operation)
        logger.warning(
            "CrowdStrike %s returned HTTP %s; retrying (attempt %d of %d).",
            operation,
            status_code,
            attempt,
            attempts,
        )
        time.sleep(backoff_seconds * 2 ** (attempt - 1))
    return get_response_body(call(), operation)
