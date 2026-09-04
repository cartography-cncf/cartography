import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.notion.util import get_paginated
from cartography.intel.notion.util import scoped_id
from cartography.models.notion.bot import NotionBotSchema
from cartography.models.notion.user import NotionUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get(api_session: requests.Session) -> list[dict[str, Any]]:
    return get_paginated(api_session, "users")


def transform(
    users: list[dict[str, Any]],
    workspace_id: str,
    token_user: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    people: list[dict[str, Any]] = []
    bots: list[dict[str, Any]] = []

    token_user_id = token_user.get("id")
    if not isinstance(token_user_id, str) or not token_user_id:
        raise ValueError("Notion current bot response is missing a valid id")
    users_by_id = {user.get("id"): user for user in users}
    users_by_id[token_user_id] = token_user

    for user in users_by_id.values():
        notion_user_id = user.get("id")
        user_type = user.get("type")
        if not isinstance(notion_user_id, str) or not notion_user_id:
            raise ValueError("Notion user response is missing a valid id")
        if not isinstance(user_type, str) or not user_type:
            raise ValueError("Notion user response is missing a valid type")
        if user_type == "person":
            person = user.get("person")
            if person is None:
                person = {}
            if not isinstance(person, dict):
                raise ValueError("Notion person response must contain an object")
            email = person.get("email")
            people.append(
                {
                    "id": scoped_id(workspace_id, notion_user_id),
                    "notion_user_id": notion_user_id,
                    "name": user.get("name"),
                    "email": email.lower() if isinstance(email, str) else None,
                    "is_workspace_member": True,
                },
            )
        elif user_type == "bot":
            bot = user.get("bot")
            if bot is None:
                bot = {}
            if not isinstance(bot, dict):
                raise ValueError("Notion bot response must contain an object")
            owner = bot.get("owner")
            if owner is None:
                owner = {}
            if not isinstance(owner, dict):
                raise ValueError("Notion bot owner must be an object")
            owner_type = owner.get("type")
            owner_user = owner.get("user")
            if owner_user is None:
                owner_user = {}
            if not isinstance(owner_user, dict):
                raise ValueError("Notion bot user owner must be an object")
            owner_notion_user_id = (
                owner_user.get("id") if owner_type == "user" else None
            )
            bots.append(
                {
                    "id": scoped_id(workspace_id, notion_user_id),
                    "notion_user_id": notion_user_id,
                    "name": user.get("name"),
                    "is_token_bot": notion_user_id == token_user_id,
                    "owner_type": owner_type,
                    "owner_notion_user_id": owner_notion_user_id,
                    "owner_id": (
                        scoped_id(workspace_id, owner_notion_user_id)
                        if owner_notion_user_id
                        else None
                    ),
                },
            )
        else:
            raise ValueError(f"Unsupported Notion user type {user_type!r}")

    return people, bots


def load_users(
    neo4j_session: neo4j.Session,
    people: list[dict[str, Any]],
    bots: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NotionUserSchema(),
        people,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )
    load(
        neo4j_session,
        NotionBotSchema(),
        bots,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(NotionBotSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(NotionUserSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    workspace: dict[str, Any],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    workspace_id = workspace["id"]
    logger.info("Starting Notion identity sync")
    raw_users = get(api_session)
    people, bots = transform(raw_users, workspace_id, workspace["token_user"])
    load_users(neo4j_session, people, bots, workspace_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed Notion identity sync")
