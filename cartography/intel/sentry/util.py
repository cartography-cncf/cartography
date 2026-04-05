import logging
import re
from typing import Any

import requests

from cartography.helpers import backoff_handler
from cartography.util import retries_with_backoff

logger = logging.getLogger(__name__)

_TIMEOUT = (60, 60)
_LINK_NEXT_RE = re.compile(
    r'<([^>]+)>;\s*rel="next";\s*results="(\w+)";\s*cursor="([^"]+)"',
)


def call_sentry_api(
    api_session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
) -> requests.Response:
    wrapped = retries_with_backoff(
        func=_call_sentry_api_base,
        exception_type=requests.exceptions.RequestException,
        max_tries=5,
        on_backoff=backoff_handler,
    )
    return wrapped(api_session, url, params)


def _call_sentry_api_base(
    api_session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
) -> requests.Response:
    response = api_session.get(url, params=params, timeout=_TIMEOUT)
    response.raise_for_status()
    return response


def get_paginated_results(
    api_session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Paginate through Sentry API results using cursor-based Link headers."""
    all_results: list[dict[str, Any]] = []
    next_url: str | None = url
    next_params = params

    while next_url:
        response = call_sentry_api(api_session, next_url, next_params)
        all_results.extend(response.json())

        # After the first request, cursor is embedded in the next URL
        next_params = None
        next_url = _get_next_url(response)

    return all_results


def _get_next_url(response: requests.Response) -> str | None:
    """Parse the Link header to find the next page URL."""
    link_header = response.headers.get("Link", "")
    match = _LINK_NEXT_RE.search(link_header)
    if match and match.group(2) == "true":
        return match.group(1)
    return None
