"""
Bitbucket Cloud Intel Module Utilities

Retry/backoff and paginated fetch helpers for the Bitbucket Cloud REST API.
"""

import logging
import time
from typing import Any

import requests

from cartography.intel.bitbucket.auth import BitbucketCredential

logger = logging.getLogger(__name__)

BASE_URL = "https://api.bitbucket.org/2.0"

DEFAULT_MAX_RETRIES = 5
DEFAULT_TIMEOUT = 30
DEFAULT_RETRY_BACKOFF_BASE = 2
DEFAULT_PAGE_LEN = 100


def make_request_with_retry(
    method: str,
    url: str,
    headers: dict[str, str],
    params: dict[str, Any] | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout: int = DEFAULT_TIMEOUT,
) -> requests.Response:
    """Make an HTTP request, retrying on 429s and 5xxs with backoff."""
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

            if response.status_code == 429:
                retry_after = _get_retry_after(response)
                if retry_count < max_retries:
                    logger.warning(
                        "Bitbucket rate limit hit (429). Sleeping %ss before retry (%s/%s)",
                        retry_after,
                        retry_count + 1,
                        max_retries,
                    )
                    time.sleep(retry_after)
                    retry_count += 1
                    continue
                response.raise_for_status()

            if response.status_code >= 500:
                if retry_count < max_retries:
                    sleep_time = DEFAULT_RETRY_BACKOFF_BASE**retry_count
                    logger.warning(
                        "Bitbucket server error (%s). Sleeping %ss before retry (%s/%s)",
                        response.status_code,
                        sleep_time,
                        retry_count + 1,
                        max_retries,
                    )
                    time.sleep(sleep_time)
                    retry_count += 1
                    continue
                response.raise_for_status()

            return response

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_exception = e
            if retry_count < max_retries:
                sleep_time = DEFAULT_RETRY_BACKOFF_BASE**retry_count
                logger.warning(
                    "Bitbucket request error (%s). Sleeping %ss before retry (%s/%s)",
                    e,
                    sleep_time,
                    retry_count + 1,
                    max_retries,
                )
                time.sleep(sleep_time)
                retry_count += 1
            else:
                raise

    if last_exception:
        raise last_exception
    raise requests.exceptions.RequestException("Request failed after all retries")


def strip_uuid(raw_uuid: str) -> str:
    """Bitbucket UUIDs are wrapped in curly braces, e.g. "{...}" - strip them."""
    return raw_uuid.strip("{}")


def _get_retry_after(response: requests.Response) -> int:
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        try:
            return int(retry_after)
        except ValueError:
            pass
    return 60


def _auth_headers(credential: BitbucketCredential) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {credential.get_token()}",
        "Accept": "application/json",
    }


def get_single(
    credential: BitbucketCredential,
    endpoint: str,
) -> dict[str, Any]:
    """Fetch a single item from a Bitbucket Cloud API endpoint."""
    url = f"{BASE_URL}{endpoint}"
    response = make_request_with_retry("GET", url, _auth_headers(credential))
    response.raise_for_status()
    result: dict[str, Any] = response.json()
    return result


def get_paginated(
    credential: BitbucketCredential,
    endpoint: str,
    extra_params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch all pages from a Bitbucket Cloud API endpoint.

    Bitbucket paginates via a "next" field in the response body holding a full
    URL for the next page (absent on the last page), not a header like GitLab.
    """
    params: dict[str, Any] | None = {
        "pagelen": DEFAULT_PAGE_LEN,
        **(extra_params or {}),
    }
    url: str | None = f"{BASE_URL}{endpoint}"
    results: list[dict[str, Any]] = []

    while url:
        response = make_request_with_retry(
            "GET", url, _auth_headers(credential), params
        )
        response.raise_for_status()
        page = response.json()
        results.extend(page.get("values", []))
        next_url = page.get("next")
        if next_url is not None and (not isinstance(next_url, str) or not next_url):
            raise ValueError(f"Malformed Bitbucket pagination link: {next_url!r}")
        url = next_url
        params = None  # `next` already encodes cursor state

    return results
