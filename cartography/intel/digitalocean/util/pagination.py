# utils/pagination.py

from collections.abc import Callable, MutableMapping
from typing import Any


def get_paginated_list(
    list_function: Callable[..., MutableMapping[str, Any]],
    target_key: str,
    max_pages: int = 100,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """
        Retrieves a paginated list of items from a DigitalOcean API endpoint.
        If there is no next page, then it's the last page and the functino will stop fetching more pages.
        Default per_page is 20, and current max_pages is set to 100 to limit the number of API calls. 
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

    for page_num in range(1, max_pages + 1):
        result = list_function(page=page_num, **kwargs)
        data.extend(result.get(target_key, []))

        if not result.get("links", {}).get("pages", {}).get("next"):
            break

    return data
