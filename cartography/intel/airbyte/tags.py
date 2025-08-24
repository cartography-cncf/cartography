import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.airbyte.util import AirbyteClient
from cartography.models.airbyte.tag import AirbyteTagSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: AirbyteClient,
    org_id: str,
    workspace_ids: List[str],
    common_job_parameters: Dict[str, Any],
) -> None:
    tags = get(api_session, workspace_ids)
    load_tags(neo4j_session, tags, org_id, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: AirbyteClient,
    workspace_ids: List[str],
) -> List[Dict[str, Any]]:
    return api_session.get(
        "/tags",
        params={"workspaceIds": ",".join(workspace_ids)} if workspace_ids else None,
    )


@timeit
def load_tags(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Airbyte Tags into Neo4j.", len(data))
    load(
        neo4j_session,
        AirbyteTagSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(AirbyteTagSchema(), common_job_parameters).run(
        neo4j_session
    )
