import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.zendesk.api_token import ZendeskAPITokenSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    subdomain: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    tokens = get(session, subdomain)
    if tokens is None:
        return
    data = transform(tokens, subdomain)
    load_api_tokens(neo4j_session, data, subdomain, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(session: requests.Session, subdomain: str) -> list[dict[str, Any]] | None:
    """Return an empty inventory on 404, or None on 403 to preserve prior data."""
    # ListApiTokens is an unpaginated collection in Zendesk's official OpenAPI spec.
    response = session.get(
        f"https://{subdomain}.zendesk.com/api/v2/api_tokens.json",
        params={"include_users": "true"},
        timeout=(60, 60),
        allow_redirects=False,
    )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            logger.info(
                "API token access is disabled for Zendesk account %s (404). "
                "Removing previously ingested API tokens.",
                subdomain,
            )
            return []
        if exc.response is not None and exc.response.status_code == 403:
            logger.warning(
                "Permission denied reading API tokens for Zendesk account %s (403). "
                "Skipping API token load and cleanup; preserving prior inventory.",
                subdomain,
            )
            return None
        raise
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
            "assigned_user_node_id": (
                f"{subdomain}:{token['assigned_user_id']}"
                if token.get("assigned_user_id") is not None
                else None
            ),
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
