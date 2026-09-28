import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.modal.util import list_service_users
from cartography.intel.modal.util import ModalClient
from cartography.models.modal.api_token import ModalApiTokenSchema
from cartography.models.modal.service_user import ModalServiceUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    client: ModalClient,
    common_job_parameters: dict[str, Any],
    user_ids_by_username: dict[str, str],
) -> list[dict[str, Any]]:
    """Ingest service users and their API tokens.

    Each Modal service user owns exactly one API token, but they are modelled as separate
    nodes so the token carries its own last-used timestamp and so the canonical
    APIKey -> ServiceAccount OWNED_BY edge exists for cross-provider rules.
    """
    raw = await list_service_users(client)
    workspace_id = common_job_parameters["WORKSPACE_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    service_users = transform(raw, user_ids_by_username)
    load_service_users(neo4j_session, service_users, workspace_id, update_tag)

    tokens = transform_tokens(raw)
    load_api_tokens(neo4j_session, tokens, workspace_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)
    return service_users


def transform(
    raw: list[dict[str, Any]], user_ids_by_username: dict[str, str]
) -> list[dict[str, Any]]:
    return [
        {
            "id": user["id"],
            "name": user.get("name"),
            "created_at": user.get("created_at"),
            "created_by": user.get("created_by"),
            # Resolved against this workspace's members only, so a username that also exists in
            # another synced workspace cannot attract the edge. None when the creator is no
            # longer a member, which simply leaves the CREATED_BY edge absent.
            "created_by_user_id": user_ids_by_username.get(
                user.get("created_by") or ""
            ),
        }
        for user in raw
    ]


def transform_tokens(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tokens = []
    for user in raw:
        token_id = user.get("token_id")
        if not token_id:
            # A service user should always have a token; if Modal ever returns one without,
            # skip it rather than creating a token node with no identity.
            logger.warning(
                "Modal service user %s has no token id; skipping its API token node.",
                user["id"],
            )
            continue
        tokens.append(
            {
                "id": token_id,
                "token_id": token_id,
                "name": user.get("name"),
                "created_at": user.get("created_at"),
                "last_used_at": user.get("last_used_at"),
                "service_user_id": user["id"],
            }
        )
    return tokens


@timeit
def load_service_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalServiceUserSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def load_api_tokens(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalApiTokenSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(ModalApiTokenSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(ModalServiceUserSchema(), common_job_parameters).run(
        neo4j_session
    )
