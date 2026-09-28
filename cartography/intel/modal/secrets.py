import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.modal.util import list_secrets
from cartography.intel.modal.util import ModalClient
from cartography.models.modal.secret import ModalSecretSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    client: ModalClient,
    common_job_parameters: dict[str, Any],
    user_ids_by_username: dict[str, str],
) -> list[dict[str, Any]]:
    """Ingest the secrets of one environment.

    Only metadata: Modal returns no secret values through any read API."""
    environment_name = common_job_parameters["ENVIRONMENT_NAME"]
    raw = await list_secrets(client, environment_name)
    items = transform(raw, environment_name, user_ids_by_username)
    load_secrets(
        neo4j_session,
        items,
        common_job_parameters["ENVIRONMENT_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return items


def transform(
    raw: list[dict[str, Any]],
    environment_name: str,
    user_ids_by_username: dict[str, str],
) -> list[dict[str, Any]]:
    return [
        {
            **item,
            "environment_name": environment_name,
            # Resolved against this workspace's members only, so a username that also exists in
            # another synced workspace cannot attract the edge. None when the creator is no
            # longer a member, which simply leaves the CREATED_BY edge absent.
            "created_by_user_id": user_ids_by_username.get(
                item.get("created_by") or ""
            ),
        }
        for item in raw
    ]


@timeit
def load_secrets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    environment_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalSecretSchema(),
        data,
        lastupdated=update_tag,
        ENVIRONMENT_ID=environment_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(ModalSecretSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_for_environment(
    neo4j_session: neo4j.Session,
    workspace_id: str,
    environment_id: str,
    update_tag: int,
) -> None:
    """Tear down this resource for one environment, by id. See `environments` for why."""
    cleanup(
        neo4j_session,
        {
            "UPDATE_TAG": update_tag,
            "WORKSPACE_ID": workspace_id,
            "ENVIRONMENT_ID": environment_id,
        },
    )
