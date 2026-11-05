import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.langsmith.util import LangSmithClient
from cartography.models.langsmith.workspace import LangSmithWorkspaceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: LangSmithClient,
    org_id: str,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    workspaces = get(client, org_id)
    load_workspaces(
        neo4j_session, workspaces, org_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)
    return workspaces


@timeit
def get(client: LangSmithClient, org_id: str) -> list[dict[str, Any]]:
    return client.get("/api/v1/workspaces", org_id=org_id)


@timeit
def load_workspaces(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        LangSmithWorkspaceSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(LangSmithWorkspaceSchema(), common_job_parameters).run(
        neo4j_session
    )
