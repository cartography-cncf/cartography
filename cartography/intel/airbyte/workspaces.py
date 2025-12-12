import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.airbyte.util import AirbyteClient
from cartography.models.airbyte.workspace import AirbyteWorkspaceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: AirbyteClient,
    org_id: str,
    common_job_parameters: Dict[str, Any],
) -> List[Dict[str, Any]]:
    workspaces = get(api_session, org_id)
    load_workspaces(
        neo4j_session, workspaces, org_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)
    return workspaces


@timeit
def get(
    api_session: AirbyteClient,
    org_id: str,
) -> List[Dict[str, Any]]:
    return api_session.get("/workspaces", params={"organizationId": org_id})


@timeit
def load_workspaces(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Airbyte Workspaces into Neo4j.", len(data))
    load(
        neo4j_session,
        AirbyteWorkspaceSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(AirbyteWorkspaceSchema(), common_job_parameters).run(
        neo4j_session
    )
