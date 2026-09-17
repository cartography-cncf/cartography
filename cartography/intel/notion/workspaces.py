from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.intel.notion.util import NOTION_API_BASE_URL
from cartography.intel.notion.util import REQUEST_TIMEOUT
from cartography.intel.notion.util import require_nonempty_string
from cartography.intel.notion.util import require_object
from cartography.models.notion.workspace import NotionWorkspaceSchema
from cartography.util import timeit


@timeit
def get(api_session: requests.Session) -> dict[str, Any]:
    response = api_session.get(
        f"{NOTION_API_BASE_URL}/users/me",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return require_object(response.json(), "Notion current-user response")


def transform(token_user: dict[str, Any]) -> dict[str, Any]:
    if token_user.get("object") != "user":
        raise ValueError("Notion current bot response has an unexpected object type")
    if token_user.get("type") != "bot":
        raise ValueError(
            "Notion personal access tokens cannot list workspace users; "
            "configure an internal or public connection token instead"
        )

    notion_bot_id = require_nonempty_string(
        token_user.get("id"),
        "Notion current bot id",
    )
    bot = require_object(token_user.get("bot"), "Notion current bot details")
    workspace_id = require_nonempty_string(
        bot.get("workspace_id"),
        "Notion current bot workspace id",
    )
    workspace_name = bot.get("workspace_name")
    if workspace_name is not None:
        workspace_name = require_nonempty_string(
            workspace_name,
            "Notion current bot workspace name",
        )

    return {
        "id": workspace_id,
        "name": workspace_name or workspace_id,
        "token_bot_notion_user_id": notion_bot_id,
    }


@timeit
def sync(
    neo4j_session: neo4j.Session,
    workspace: dict[str, Any],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NotionWorkspaceSchema(),
        [workspace],
        lastupdated=update_tag,
    )
