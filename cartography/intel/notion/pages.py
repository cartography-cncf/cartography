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
from cartography.intel.notion.util import require_boolean
from cartography.intel.notion.util import require_nonempty_string
from cartography.intel.notion.util import require_object
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
    for raw_value in properties.values():
        value = require_object(raw_value, "Notion page property")
        if value.get("type") != "title":
            continue
        title = value.get("title")
        if not isinstance(title, list):
            raise ValueError("Notion page title must be a list")
        plain_text_parts = []
        for raw_item in title:
            item = require_object(raw_item, "Notion page title item")
            plain_text = item.get("plain_text")
            if not isinstance(plain_text, str):
                raise ValueError("Notion page title plain_text must be a string")
            plain_text_parts.append(plain_text)
        return "".join(plain_text_parts) or None
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
        notion_page_id = require_nonempty_string(
            page.get("id"),
            "Notion page id",
        )
        if "public_url" not in page:
            raise ValueError("Notion page response is missing public_url")
        public_url = page["public_url"]
        if public_url is not None:
            public_url = require_nonempty_string(
                public_url,
                "Notion page public_url",
            )

        created_time = require_nonempty_string(
            page.get("created_time"),
            "Notion page created_time",
        )
        last_edited_time = require_nonempty_string(
            page.get("last_edited_time"),
            "Notion page last_edited_time",
        )
        url = require_nonempty_string(page.get("url"), "Notion page url")
        in_trash = require_boolean(page.get("in_trash"), "Notion page in_trash")
        is_locked = require_boolean(page.get("is_locked"), "Notion page is_locked")

        created_by = require_object(
            page.get("created_by"),
            "Notion page created_by",
        )
        parent = require_object(page.get("parent"), "Notion page parent")
        properties = require_object(page.get("properties"), "Notion page properties")
        created_by_notion_user_id = require_nonempty_string(
            created_by.get("id"),
            "Notion page creator id",
        )
        parent_type = require_nonempty_string(
            parent.get("type"),
            "Notion page parent type",
        )
        parent_notion_id = (
            None
            if parent_type == "workspace"
            else require_nonempty_string(
                parent.get(parent_type),
                "Notion page parent id",
            )
        )

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
    # Keep graph updates staged until every response page is valid.
    with (
        tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as staged_pages,
        tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as staged_deletes,
    ):
        for raw_pages in get(api_session):
            public_pages, unpublished_page_ids = transform(raw_pages, workspace_id)
            public_page_count += len(public_pages)
            unpublished_page_count += len(unpublished_page_ids)
            if public_pages:
                staged_pages.write(json.dumps(public_pages))
                staged_pages.write("\n")
            for page_id in unpublished_page_ids:
                staged_deletes.write(json.dumps(page_id))
                staged_deletes.write("\n")

        staged_pages.seek(0)
        for line in staged_pages:
            load_pages(neo4j_session, json.loads(line), workspace_id, update_tag)

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
