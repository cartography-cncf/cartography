# utils/pagination.py

from collections.abc import Callable
from collections.abc import MutableMapping
from typing import Any

DEFAULT_MAX_PAGES = 10000
DEFAULT_PER_PAGE = 200  # DigitalOcean API maximum per-page size


def get_paginated_list(
    list_function: Callable[..., MutableMapping[str, Any]],
    target_key: str,
    max_pages: int | None = DEFAULT_MAX_PAGES,
    per_page: int = DEFAULT_PER_PAGE,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """
    Retrieves a paginated list of items from a DigitalOcean API endpoint.
    If there is no next page, then it's the last page and the functino will stop fetching more pages.
    Default per_page is 200, and current max_pages is set to 10000 to limit the number of API calls.
    e.g.
    {
        "<target_key>": [<list of items>],
        "links": {
            "pages": {
            "next": "https://api.digitalocean.com/v2/tags?page=2",
            "prev": "https://api.digitalocean.com/v2/tags?page=1",
            "first": "https://api.digitalocean.com/v2/tags?page=1",
            "last": "https://api.digitalocean.com/v2/tags?page=3"
            }
        }
    }
    """
    data: list[dict[str, Any]] = []

    if max_pages is not None and max_pages <= 0:
        raise ValueError("max_pages must be positive or None.")

    page_num = 1

    while True:
        result = list_function(page=page_num, per_page=per_page, **kwargs)

        if target_key not in result:
            raise RuntimeError(f"Expected key '{target_key}' in paginated response.")

        data.extend(result[target_key])

        if not result.get("links", {}).get("pages", {}).get("next"):
            break

        if max_pages is not None and page_num >= max_pages:
            raise RuntimeError(
                f"Reached maximum page limit of {max_pages} while more pages are available."
            )

        page_num += 1

    return data
