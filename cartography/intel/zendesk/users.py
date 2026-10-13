from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.zendesk.util import get_paginated
from cartography.models.zendesk.user import ZendeskUserSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    subdomain: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    users = get(session, subdomain)
    transformed_users = transform(users, subdomain)
    load_users(neo4j_session, transformed_users, subdomain, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(session: requests.Session, subdomain: str) -> list[dict[str, Any]]:
    return get_paginated(
        session,
        subdomain,
        "users",
        "users",
        {"role[]": ["agent", "admin"]},
    )


def transform(users: list[dict[str, Any]], subdomain: str) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{subdomain}:{user['id']}",
            "user_id": user["id"],
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user["role"],
            "role_type": user.get("role_type"),
            "custom_role_id": user.get("custom_role_id"),
            "active": user.get("active"),
            "suspended": user.get("suspended"),
            "created_at": user.get("created_at"),
            "updated_at": user.get("updated_at"),
            "last_login_at": user.get("last_login_at"),
        }
        for user in users
        if user["role"] in ("agent", "admin")
    ]


def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subdomain: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ZendeskUserSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=subdomain,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(ZendeskUserSchema(), common_job_parameters).run(
        neo4j_session
    )
