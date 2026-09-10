import json
import logging
import tempfile
from collections.abc import Iterator
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
from cartography.intel.notion.util import post_paginated
from cartography.intel.notion.util import scoped_id
from cartography.models.notion.page import NotionPageSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get(
    api_session: requests.Session,
) -> Iterator[list[dict[str, Any]]]:
    return post_paginated(
        api_session,
        "search",
        {"filter": {"property": "object", "value": "page"}},
        "page_or_data_source",
    )


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
) -> tuple[list[dict[str, Any]], list[str]]:
    public_pages: list[dict[str, Any]] = []
    unpublished_page_ids: list[str] = []

    for page in pages:
        if page.get("object") != "page":
            raise ValueError("Notion page search returned a non-page object")
        notion_page_id = page.get("id")
        if not isinstance(notion_page_id, str) or not notion_page_id:
            raise ValueError("Notion page response is missing a valid id")
        if "public_url" not in page:
            raise ValueError("Notion page response is missing public_url")
        public_url = page["public_url"]
        if public_url is not None and (
            not isinstance(public_url, str) or not public_url
        ):
            raise ValueError(
                "Notion page public_url must be a non-empty string or null"
            )

        created_time = page.get("created_time")
        last_edited_time = page.get("last_edited_time")
        url = page.get("url")
        in_trash = page.get("in_trash")
        is_locked = page.get("is_locked")
        if not isinstance(created_time, str) or not created_time:
            raise ValueError("Notion page response is missing created_time")
        if not isinstance(last_edited_time, str) or not last_edited_time:
            raise ValueError("Notion page response is missing last_edited_time")
        if not isinstance(url, str) or not url:
            raise ValueError("Notion page response is missing a valid url")
        if not isinstance(in_trash, bool):
            raise ValueError("Notion page response is missing boolean in_trash")
        if not isinstance(is_locked, bool):
            raise ValueError("Notion page response is missing boolean is_locked")

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
        if (
            not isinstance(created_by_notion_user_id, str)
            or not created_by_notion_user_id
        ):
            raise ValueError("Notion page creator is missing a valid id")
        parent_type = parent.get("type")
        if not isinstance(parent_type, str) or not parent_type:
            raise ValueError("Notion page parent is missing a valid type")
        parent_notion_id = parent.get(parent_type)
        if not isinstance(parent_notion_id, str):
            parent_notion_id = None

        if public_url is None:
            unpublished_page_ids.append(scoped_id(workspace_id, notion_page_id))
            continue

        public_pages.append(
            {
                "id": scoped_id(workspace_id, notion_page_id),
                "notion_page_id": notion_page_id,
                "title": _get_title(properties),
                "url": url,
                "public_url": public_url,
                "is_public": True,
                "created_time": created_time,
                "last_edited_time": last_edited_time,
                "in_trash": in_trash,
                "is_locked": is_locked,
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
    public_page_count = 0
    unpublished_page_count = 0
    # Search is non-authoritative, so only explicit null public URLs drive cleanup.
    # Keep those destructive updates staged until every response page is valid.
    with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as staged_deletes:
        for raw_pages in get(api_session):
            public_pages, unpublished_page_ids = transform(raw_pages, workspace_id)
            load_pages(neo4j_session, public_pages, workspace_id, update_tag)
            public_page_count += len(public_pages)
            unpublished_page_count += len(unpublished_page_ids)
            for page_id in unpublished_page_ids:
                staged_deletes.write(json.dumps(page_id))
                staged_deletes.write("\n")

        staged_deletes.seek(0)
        delete_batch: list[str] = []
        for line in staged_deletes:
            delete_batch.append(json.loads(line))
            if len(delete_batch) == 10_000:
                delete_confirmed_unpublished_pages(neo4j_session, delete_batch)
                delete_batch = []
        delete_confirmed_unpublished_pages(neo4j_session, delete_batch)
    logger.info(
        "Loaded %d public Notion pages and observed %d unpublished pages",
        public_page_count,
        unpublished_page_count,
    )
    logger.info("Completed Notion public page sync")
