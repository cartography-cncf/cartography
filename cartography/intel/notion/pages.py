import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import read_list_of_values_tx
from cartography.client.core.tx import run_write_query
from cartography.intel.notion.util import post_paginated
from cartography.intel.notion.util import scoped_id
from cartography.models.notion.page import NotionPageSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_existing_page_ids(
    neo4j_session: neo4j.Session,
    workspace_id: str,
) -> list[str]:
    query = """
    MATCH (:NotionWorkspace {id: $WORKSPACE_ID})-[:RESOURCE]->(p:NotionPage)
    RETURN p.notion_page_id
    """
    return [
        str(page_id)
        for page_id in neo4j_session.execute_read(
            read_list_of_values_tx,
            query,
            WORKSPACE_ID=workspace_id,
        )
    ]


def get(
    api_session: requests.Session,
) -> list[dict[str, Any]]:
    search_results = post_paginated(
        api_session,
        "search",
        {"filter": {"property": "object", "value": "page"}},
    )
    for page in search_results:
        notion_page_id = page.get("id")
        if not isinstance(notion_page_id, str) or not notion_page_id:
            raise ValueError("Notion search page is missing a valid id")
    return search_results


def _get_title(properties: dict[str, Any]) -> str | None:
    for value in properties.values():
        if not isinstance(value, dict) or value.get("type") != "title":
            continue
        title = value.get("title")
        if not isinstance(title, list):
            return None
        return "".join(
            item.get("plain_text", "")
            for item in title
            if isinstance(item, dict) and isinstance(item.get("plain_text", ""), str)
        )
    return None


def transform(
    pages: list[dict[str, Any]],
    workspace_id: str,
    existing_page_ids: set[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    public_pages: list[dict[str, Any]] = []
    unpublished_page_ids: list[str] = []

    for page in pages:
        if page.get("object") != "page":
            raise ValueError("Notion page search returned a non-page object")
        notion_page_id = page.get("id")
        public_url = page.get("public_url")
        if not isinstance(notion_page_id, str) or not notion_page_id:
            raise ValueError("Notion page response is missing a valid id")
        if public_url is None:
            if notion_page_id in existing_page_ids:
                unpublished_page_ids.append(scoped_id(workspace_id, notion_page_id))
            continue
        if not isinstance(public_url, str) or not public_url:
            raise ValueError(
                "Notion page public_url must be a non-empty string or null"
            )

        created_by = page.get("created_by")
        parent = page.get("parent")
        properties = page.get("properties")
        if not isinstance(created_by, dict):
            raise ValueError("Notion page response must contain a created_by object")
        if not isinstance(parent, dict):
            raise ValueError("Notion page response must contain a parent object")
        if not isinstance(properties, dict):
            raise ValueError("Notion page response must contain a properties object")
        created_by_notion_user_id = created_by.get("id")
        if not isinstance(created_by_notion_user_id, str):
            raise ValueError("Notion page creator is missing a valid id")
        parent_type = parent.get("type")
        if not isinstance(parent_type, str):
            raise ValueError("Notion page parent is missing a valid type")
        parent_notion_id = parent.get(parent_type)
        if not isinstance(parent_notion_id, str):
            parent_notion_id = None

        public_pages.append(
            {
                "id": scoped_id(workspace_id, notion_page_id),
                "notion_page_id": notion_page_id,
                "title": _get_title(properties),
                "url": page.get("url"),
                "public_url": public_url,
                "is_public": True,
                "created_time": page.get("created_time"),
                "last_edited_time": page.get("last_edited_time"),
                "in_trash": page.get("in_trash"),
                "is_locked": page.get("is_locked"),
                "parent_type": parent_type,
                "parent_notion_id": parent_notion_id,
                "created_by_notion_user_id": created_by_notion_user_id,
                "created_by_id": scoped_id(
                    workspace_id,
                    created_by_notion_user_id,
                ),
            }
        )

    return public_pages, unpublished_page_ids


def load_pages(
    neo4j_session: neo4j.Session,
    pages: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NotionPageSchema(),
        pages,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


def delete_confirmed_unpublished_pages(
    neo4j_session: neo4j.Session,
    page_ids: list[str],
) -> None:
    if not page_ids:
        return
    run_write_query(
        neo4j_session,
        """
        MATCH (p:NotionPage)
        WHERE p.id IN $PAGE_IDS
        DETACH DELETE p
        """,
        PAGE_IDS=page_ids,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    workspace_id: str,
    update_tag: int,
) -> None:
    logger.info("Starting Notion public page sync")
    existing_page_ids = set(get_existing_page_ids(neo4j_session, workspace_id))
    # Search is not authoritative, so absence must never drive cleanup. It is also
    # important not to re-fetch every missing page because that creates an
    # unbounded request-per-page fallback for large workspaces.
    raw_pages = get(api_session)
    public_pages, unpublished_page_ids = transform(
        raw_pages,
        workspace_id,
        existing_page_ids,
    )
    load_pages(neo4j_session, public_pages, workspace_id, update_tag)
    delete_confirmed_unpublished_pages(neo4j_session, unpublished_page_ids)
    logger.info("Completed Notion public page sync")
