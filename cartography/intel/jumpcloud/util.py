import logging
import time
from typing import Any
from typing import Generator

import requests

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS_CODES = {502, 503, 504}
_MAX_RETRIES = 3


def paginated_get(
    api_session: requests.Session,
    url: str,
    headers: dict[str, str],
    timeout: tuple[int, int],
    params: dict[str, Any] | None = None,
    page_size: int = 100,
    skip_param: str = "skip",
) -> Generator[dict[str, Any], None, None]:
    """Helper to get paginated data from the JumpCloud API using skip-based pagination.

    Handles both list responses and dict responses with a 'results' or 'data' key.
    For list responses, continues paginating as long as a full page is returned.
    For dict responses, continues until an empty page is returned.

    Args:
        api_session: The requests session to use for making API calls.
        url: The URL to make the API call to.
        headers: Auth headers to include with each request.
        timeout: The timeout for the API call.
        params: Additional query parameters to merge into each request.
        page_size: Number of items to request per page.

    Yields:
        Individual result dictionaries from the API response.
    """
    base_params: dict[str, Any] = dict(params or {})
    skip = 0
    while True:
        for attempt in range(_MAX_RETRIES):
            response = api_session.get(
                url,
                headers=headers,
                params={**base_params, "limit": page_size, skip_param: skip},
                timeout=timeout,
            )
            if response.status_code not in _RETRYABLE_STATUS_CODES:
                break
            wait = 2 ** attempt
            logger.warning(
                "Got %d from %s (skip=%d), retrying in %ds (attempt %d/%d)",
                response.status_code, url, skip, wait, attempt + 1, _MAX_RETRIES,
            )
            time.sleep(wait)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            page_len = len(payload)
            logger.debug("paginated_get %s skip=%d got %d items", url, skip, page_len)
            yield from payload
            if page_len < page_size:
                logger.debug("paginated_get %s done (last page had %d items)", url, page_len)
                break
        else:
            page: list[dict[str, Any]] = []
            for key in ("results", "data"):
                value = payload.get(key)
                if isinstance(value, list):
                    page = value
                    break
            page_len = len(page)
            logger.debug("paginated_get %s skip=%d got %d items", url, skip, page_len)
            if not page:
                logger.debug("paginated_get %s done (empty page)", url)
                break
            yield from page
        skip += page_size
