import logging
from typing import Any

from slack_sdk import WebClient

from cartography.intel.pagination import get_pagination_limits

logger = logging.getLogger(__name__)
MAX_PAGINATION_PAGES, MAX_PAGINATION_ITEMS = get_pagination_limits(logger)


def slack_paginate(
    slack_client: WebClient,
    endpoint: str,
    data_key: str,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    endpoint_method = getattr(slack_client, endpoint)
    page_count = 0

    # First query
    response = endpoint_method(**kwargs)
    items.extend(response.get(data_key, []))
    page_count += 1
    if len(items) > MAX_PAGINATION_ITEMS:
        logger.warning(
            "Slack: reached max pagination items (%d). Stopping after %d pages.",
            MAX_PAGINATION_ITEMS,
            page_count,
        )
        return items

    # Iterate over the cursor
    cursor = response.get("response_metadata", {}).get("next_cursor")
    while cursor:
        if page_count >= MAX_PAGINATION_PAGES:
            logger.warning(
                "Slack: reached max pagination pages (%d). Stopping with %d items.",
                MAX_PAGINATION_PAGES,
                len(items),
            )
            break
        if len(items) >= MAX_PAGINATION_ITEMS:
            logger.warning(
                "Slack: reached max pagination items (%d). Stopping after %d pages.",
                MAX_PAGINATION_ITEMS,
                page_count,
            )
            break
        kwargs["cursor"] = cursor
        response = endpoint_method(**kwargs)
        items.extend(response.get(data_key, []))
        page_count += 1
        if len(items) > MAX_PAGINATION_ITEMS:
            logger.warning(
                "Slack: reached max pagination items (%d). Stopping after %d pages.",
                MAX_PAGINATION_ITEMS,
                page_count,
            )
            break
        cursor = response.get("response_metadata", {}).get("next_cursor")

    return items
