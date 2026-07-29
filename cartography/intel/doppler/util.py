from typing import Any

import requests

# Connect and read timeouts of 60 seconds each; see
# https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)

# Doppler paginated endpoints default to per_page=20; request the max page size to
# keep the number of round trips down.
_PER_PAGE = 100


def paginated_get(
    api_session: requests.Session,
    url: str,
    results_key: str,
    params: dict[str, Any] | None = None,
    timeout: tuple[int, int] = _TIMEOUT,
) -> list[dict[str, Any]]:
    """Fetch every page of a paginated Doppler list endpoint.

    Doppler wraps list results under a resource-specific key (e.g. ``projects``,
    ``configs``) and paginates with ``page`` / ``per_page``. We request pages
    starting at 1 until a page returns fewer than ``per_page`` items.

    Args:
        api_session: Authenticated requests session.
        url: Full endpoint URL.
        results_key: The key under which the list of items is returned.
        params: Extra query parameters (e.g. ``{"project": "..."}``).
        timeout: ``(connect, read)`` timeout tuple.
    Returns:
        The concatenated list of item dictionaries across all pages.
    """
    results: list[dict[str, Any]] = []
    page = 1
    base_params = dict(params or {})
    while True:
        req = api_session.get(
            url,
            params={**base_params, "page": page, "per_page": _PER_PAGE},
            timeout=timeout,
        )
        req.raise_for_status()
        body = req.json()
        # Fail fast if the expected list key is missing: a silent fallback to [] would
        # mask an API shape / auth change and could trigger destructive cleanup of an
        # otherwise-populated node type. An explicitly empty list is fine.
        if not isinstance(body, dict) or results_key not in body:
            raise ValueError(
                f"Doppler response from {url} is missing the expected "
                f"'{results_key}' key; got keys: "
                f"{sorted(body) if isinstance(body, dict) else type(body).__name__}",
            )
        page_results = body[results_key] or []
        results.extend(page_results)
        if len(page_results) < _PER_PAGE:
            break
        page += 1
    return results
