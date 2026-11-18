import logging
from collections import defaultdict
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.onepassword.user import OnePasswordServiceAccountSchema
from cartography.models.onepassword.user import OnePasswordUserSchema

logger = logging.getLogger(__name__)

SERVICE_ACCOUNT_TYPE = "SERVICE_ACCOUNT"


def is_service_account(user: dict[str, Any]) -> bool:
    return user.get("type") == SERVICE_ACCOUNT_TYPE


def transform(
    snapshot: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split the snapshot's principals into people and service accounts."""
    group_ids: dict[str, list[str]] = defaultdict(list)
    for membership in snapshot["group_memberships"]:
        group_ids[membership["user_id"]].append(membership["group_id"])

    users: list[dict[str, Any]] = []
    service_accounts: list[dict[str, Any]] = []
    for user in snapshot["users"]:
        if is_service_account(user):
            service_accounts.append(
                {
                    "id": user["id"],
                    "name": user.get("name"),
                    "state": user.get("state"),
                    "group_ids": group_ids[user["id"]],
                },
            )
        else:
            users.append(
                {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "state": user["state"],
                    "type": user.get("type"),
                    "group_ids": group_ids[user["id"]],
                },
            )
    return users, service_accounts


def load_users(
    neo4j_session: neo4j.Session,
    users: list[dict[str, Any]],
    service_accounts: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        OnePasswordUserSchema(),
        users,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )
    load(
        neo4j_session,
        OnePasswordServiceAccountSchema(),
        service_accounts,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(OnePasswordUserSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        OnePasswordServiceAccountSchema(),
        common_job_parameters,
    ).run(neo4j_session)
