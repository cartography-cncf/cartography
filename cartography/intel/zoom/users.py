import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.helpers import normalize_email_for_matching
from cartography.intel.zoom.client import ZoomClient
from cartography.models.zoom.account import ZoomAccountSchema
from cartography.models.zoom.user import ZoomUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
PLAN_TYPES = {
    1: "Basic",
    2: "Licensed",
    4: "Unassigned without Meetings Basic",
    99: "None (legacy SSO)",
}


@timeit
def get(client: ZoomClient) -> list[dict[str, Any]]:
    users: list[dict[str, Any]] = []
    for status in ("active", "inactive", "pending"):
        params: dict[str, Any] = {"status": status, "page_size": 2000}
        seen_tokens: set[str] = set()
        count = 0
        while True:
            page = client.get_users_page(params)
            records = page["users"]
            if not isinstance(records, list):
                raise ValueError("Zoom users response must contain a list")
            users.extend({**user, "status": status} for user in records)
            count += len(records)
            next_token = page.get("next_page_token")
            if not next_token:
                if count < page.get("total_records", count):
                    raise ValueError(
                        "Zoom user pagination ended before all records were retrieved"
                    )
                break
            if next_token in seen_tokens:
                raise ValueError("Zoom returned a repeated pagination token")
            seen_tokens.add(next_token)
            params = {**params, "next_page_token": next_token}
    return users


def transform(users: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    result = {}
    for user in users:
        email = normalize_email_for_matching(user["email"])
        if not email:
            raise ValueError("Zoom user is missing a nonempty email")
        zoom_id = user.get("id")
        if zoom_id:
            node_id = f"{account_id}:user:{zoom_id}"
        elif user["status"] == "pending":
            # Pending invitations have no provider ID until activation.
            node_id = f"{account_id}:pending:{email}"
        else:
            raise ValueError("Zoom active/inactive user is missing its ID")
        result[node_id] = {
            "id": node_id,
            "zoom_id": zoom_id,
            "email": email,
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "display_name": user.get("display_name"),
            "department": user.get("dept"),
            "status": user["status"],
            "type": user["type"],
            "plan_type": PLAN_TYPES.get(user["type"]),
            "role_id": user.get("role_id"),
            "group_ids": user.get("group_ids"),
            "login_types": user.get("login_types"),
            "created_at": user.get("user_created_at"),
            "last_login_time": user.get("last_login_time"),
        }
    return list(result.values())


@timeit
def sync(
    neo4j_session: neo4j.Session, client: ZoomClient, account_id: str, update_tag: int
) -> None:
    logger.info("Syncing Zoom users")
    # Fetch and validate every status/page before any writes or stale-data cleanup.
    data = transform(get(client), account_id)
    load(
        neo4j_session, ZoomAccountSchema(), [{"id": account_id}], lastupdated=update_tag
    )
    load(
        neo4j_session,
        ZoomUserSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )
    GraphJob.from_node_schema(
        ZoomUserSchema(),
        {"UPDATE_TAG": update_tag, "ACCOUNT_ID": account_id},
    ).run(neo4j_session)
