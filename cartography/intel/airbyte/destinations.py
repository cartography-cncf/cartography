import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.airbyte.util import AirbyteClient
from cartography.intel.airbyte.util import normalize_airbyte_config
from cartography.models.airbyte.destination import AirbyteDestinationSchema
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
    destinations = get(api_session, workspace_ids)
    transformed_destinations = transform(destinations)
    load_destinations(
        neo4j_session,
        transformed_destinations,
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: AirbyteClient,
    workspace_ids: List[str],
) -> List[Dict[str, Any]]:
    return api_session.get(
        "/destinations",
        params={"workspaceIds": ",".join(workspace_ids)} if workspace_ids else None,
    )


def transform(destinations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    transformed_destinations = []
    for destination in destinations:
        destination["configuration"] = normalize_airbyte_config(
            destination.get("configuration", {})
        )
        transformed_destinations.append(destination)
    return transformed_destinations


@timeit
def load_destinations(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Airbyte Destinations into Neo4j.", len(data))
    load(
        neo4j_session,
        AirbyteDestinationSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(AirbyteDestinationSchema(), common_job_parameters).run(
        neo4j_session
    )
