import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.modal.util import list_environments
from cartography.intel.modal.util import ModalClient
from cartography.models.modal.environment import ModalEnvironmentSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    client: ModalClient,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """Ingest every environment in the workspace.

    All environments are always loaded, even when --modal-environments narrows which ones
    have their *contents* synced. `EnvironmentList` is a single cheap complete call, and
    loading only the allowlisted subset would make this workspace-scoped cleanup delete the
    other ModalEnvironment nodes while their environment-scoped children, whose cleanup
    never runs, survive as orphans.
    """
    raw = await list_environments(client)
    environments = transform(raw)
    load_environments(
        neo4j_session,
        environments,
        common_job_parameters["WORKSPACE_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return environments


def transform(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(environment) for environment in raw]


@timeit
def load_environments(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalEnvironmentSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(ModalEnvironmentSchema(), common_job_parameters).run(
        neo4j_session
    )
