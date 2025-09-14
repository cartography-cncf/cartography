from typing import Any
from typing import Generator

import requests

# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


def get_paginated(
    api_session: requests.Session,
    endpoint: str,
    items_per_page: int = 100,
    params: dict[str, Any] | None = None,
) -> Generator[dict[str, Any], None, None]:
    """Fetch paginated results from a REST API endpoint.

    This function handles pagination by making multiple requests to the API
    until all pages of results have been retrieved.

    Args:
        api_session (requests.Session): The requests session to use for making API calls.
        endpoint (str): The API endpoint to fetch data from.
        items_per_page (int, optional): The number of items to retrieve per page. Defaults to 100.
        params (dict[str, Any] | None, optional): Additional query parameters to include in the request. Defaults to None.

    Yields:
        Generator[dict[str, Any], None, None]: A generator that yields the individual items from the paginated response.
    """
    has_more = True
    offset = 0
    while has_more:
        if params is None:
            payload = {}
        else:
            payload = params.copy()
        payload["first"] = offset
        payload["max"] = items_per_page
        req = api_session.get(endpoint, params=payload, timeout=_TIMEOUT)
        req.raise_for_status()
        data = req.json()
        if not data:
            break
        yield from data
        if len(data) < items_per_page:
            has_more = False
        offset += len(data)
