from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.intel.notion.util import NOTION_API_BASE_URL
from cartography.intel.notion.util import REQUEST_TIMEOUT
from cartography.models.notion.workspace import NotionWorkspaceSchema


def get(api_session: requests.Session) -> dict[str, Any]:
    response = api_session.get(
        f"{NOTION_API_BASE_URL}/users/me",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Notion current-user response must be a JSON object")
    return payload


def transform(token_user: dict[str, Any]) -> dict[str, Any]:
    if token_user.get("type") != "bot":
        raise ValueError(
            "Notion personal access tokens cannot list workspace users; "
            "configure an internal or public connection token instead"
        )

    notion_bot_id = token_user.get("id")
    bot = token_user.get("bot")
    if not isinstance(notion_bot_id, str) or not notion_bot_id:
        raise ValueError("Notion current bot response is missing a valid id")
    if not isinstance(bot, dict):
        raise ValueError("Notion current bot response must contain bot details")

    workspace_id = bot.get("workspace_id")
    workspace_name = bot.get("workspace_name")
    if not isinstance(workspace_id, str) or not workspace_id:
        raise ValueError("Notion current bot response is missing a workspace id")
    if workspace_name is not None and not isinstance(workspace_name, str):
        raise ValueError("Notion current bot workspace name must be a string or null")

    return {
        "id": workspace_id,
        "name": workspace_name,
        "token_bot_notion_user_id": notion_bot_id,
    }


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
