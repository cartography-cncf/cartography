import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.notion.util import get_paginated
from cartography.intel.notion.util import optional_string
from cartography.intel.notion.util import require_nonempty_string
from cartography.intel.notion.util import require_object
from cartography.intel.notion.util import scoped_id
from cartography.models.notion.bot import NotionBotSchema
from cartography.models.notion.user import NotionUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(api_session: requests.Session) -> list[dict[str, Any]]:
    return get_paginated(api_session, "users", "user")


def transform(
    users: list[dict[str, Any]],
    workspace_id: str,
    token_user: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    people: list[dict[str, Any]] = []
    bots: list[dict[str, Any]] = []

    token_user_id = require_nonempty_string(
        token_user.get("id"),
        "Notion current bot id",
    )
    users_by_id = {user.get("id"): user for user in users}
    users_by_id[token_user_id] = token_user

    for user in users_by_id.values():
        if user.get("object") != "user":
            raise ValueError("Notion user response has an unexpected object type")
        notion_user_id = require_nonempty_string(
            user.get("id"),
            "Notion user id",
        )
        user_type = require_nonempty_string(
            user.get("type"),
            "Notion user type",
        )
        name = optional_string(user.get("name"), "Notion user name")
        if user_type == "person":
            person = require_object(user.get("person"), "Notion person details")
            email = optional_string(person.get("email"), "Notion person email")
            people.append(
                {
                    "id": scoped_id(workspace_id, notion_user_id),
                    "notion_user_id": notion_user_id,
                    "name": name,
                    "email": email.lower() if email is not None else None,
                    "is_workspace_member": True,
                },
            )
        elif user_type == "bot":
            bot = require_object(user.get("bot"), "Notion bot details")
            owner = bot.get("owner")
            if owner is None:
                owner = {}
            owner = require_object(owner, "Notion bot owner")
            owner_type = optional_string(
                owner.get("type"),
                "Notion bot owner type",
            )
            owner_notion_user_id = None
            if owner_type == "user":
                owner_user = require_object(
                    owner.get("user"),
                    "Notion bot user owner",
                )
                owner_notion_user_id = require_nonempty_string(
                    owner_user.get("id"),
                    "Notion bot user owner id",
                )
            bots.append(
                {
                    "id": scoped_id(workspace_id, notion_user_id),
                    "notion_user_id": notion_user_id,
                    "name": name,
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
    logger.info(
        "Loaded %d Notion users and %d Notion bot connections",
        len(people),
        len(bots),
    )
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed Notion identity sync")
