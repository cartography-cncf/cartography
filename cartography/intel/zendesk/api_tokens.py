from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.zendesk.api_token import ZendeskAPITokenSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    subdomain: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    data = transform(get(session, subdomain), subdomain)
    load_api_tokens(neo4j_session, data, subdomain, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(session: requests.Session, subdomain: str) -> list[dict[str, Any]]:
    # ListApiTokens is an unpaginated collection in Zendesk's official OpenAPI spec.
    response = session.get(
        f"https://{subdomain}.zendesk.com/api/v2/api_tokens.json",
        params={"include_users": "true"},
        timeout=(60, 60),
        allow_redirects=False,
    )
    response.raise_for_status()
    return response.json()["api_tokens"]


def transform(tokens: list[dict[str, Any]], subdomain: str) -> list[dict[str, Any]]:
    # Explicit allowlist: exclude both full token values and visible_token prefixes.
    return [
        {
            "id": f"{subdomain}:{token['id']}",
            "token_id": token["id"],
            "creator_user_id": token.get("user_id"),
            "creator_node_id": (
                f"{subdomain}:{token['user_id']}"
                if token.get("user_id") is not None
                else None
            ),
            "assigned_user_id": token.get("assigned_user_id"),
            "description": token.get("description"),
            "active": token.get("active"),
            "created_at": token.get("created_at"),
            "updated_at": token.get("updated_at"),
            "last_used": token.get("last_used"),
        }
        for token in tokens
    ]


def load_api_tokens(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subdomain: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ZendeskAPITokenSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=subdomain,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(ZendeskAPITokenSchema(), common_job_parameters).run(
        neo4j_session
    )
