from typing import Any
from typing import Callable
from typing import cast

import backoff
import requests

from cartography.helpers import backoff_handler

# Connect and read timeouts of 60 seconds each
_TIMEOUT = (60, 60)


class SentinelOnePassthroughRequestException(Exception):
    """
    Wrap a request exception that should bypass backoff and be re-raised as-is.
    """

    def __init__(self, original: requests.exceptions.RequestException):
        super().__init__(str(original))
        self.original = original


def build_scope_params(
    account_id: str | None = None,
    site_id: str | None = None,
) -> dict[str, Any]:
    """
    Build SentinelOne query params for either account-scoped or site-scoped syncs.
    """
    if site_id:
        return {"siteIds": site_id}
    if account_id:
        return {"accountIds": account_id}
    return {}


def is_site_scope_http_error(exception: Exception) -> bool:
    """
    Return True when SentinelOne rejects account enumeration for site-scoped users.
    """
    if not isinstance(exception, requests.exceptions.HTTPError):
        return False

    response = exception.response
    if response is None or response.status_code != 403:
        return False

    try:
        payload = response.json()
    except ValueError:
        return False

    if not isinstance(payload, dict):
        return False

    errors = payload.get("errors", [])
    if not isinstance(errors, list):
        return False

    for error in errors:
        if not isinstance(error, dict):
            continue
        if error.get("code") == 4030010:
            return True
        detail = str(error.get("detail", "")).lower()
        if "site users" in detail:
            return True
    return False


def is_retryable_sentinelone_exception(exception: Exception) -> bool:
    """
    Return True only for transient SentinelOne failures worth retrying.
    """
    if isinstance(
        exception,
        (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    ):
        return True

    if not isinstance(exception, requests.exceptions.HTTPError):
        return False

    response = exception.response
    if response is None:
        return False

    return response.status_code == 429 or 500 <= response.status_code < 600


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
    *,
    passthrough_exceptions: Callable[[Exception], bool] | None = None,
) -> dict[str, Any]:
    """
    Call the SentinelOne API with backoff functionality
    :param api_url: The base URL for the SentinelOne API
    :param endpoint: The API endpoint to call
    :param api_token: The API token for authentication
    :param method: The HTTP method to use (default is GET)
    :param params: Query parameters to include in the request
    :param data: Data to include in the request body for POST/PUT methods
    :param passthrough_exceptions: Optional predicate for request exceptions
        that should bypass backoff and be re-raised unchanged.
    :return: The JSON response from the API
    """

    def request_once() -> dict[str, Any]:
        try:
            return _call_sentinelone_api_base(
                api_url,
                endpoint,
                api_token,
                method,
                params,
                data,
            )
        except requests.exceptions.RequestException as exc:
            if passthrough_exceptions and passthrough_exceptions(exc):
                raise SentinelOnePassthroughRequestException(exc) from exc
            raise

    wrapped_func = cast(
        Callable[[], dict[str, Any]],
        backoff.on_exception(
            backoff.expo,
            requests.exceptions.RequestException,
            max_tries=5,  # Maximum number of retry attempts
            on_backoff=backoff_handler,
            giveup=lambda exception: not is_retryable_sentinelone_exception(exception),
        )(request_once),
    )

    try:
        return wrapped_func()
    except SentinelOnePassthroughRequestException as exc:
        raise exc.original from None


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
