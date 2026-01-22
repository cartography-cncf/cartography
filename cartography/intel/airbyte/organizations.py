import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.airbyte.util import AirbyteClient
from cartography.models.airbyte.organization import AirbyteOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: AirbyteClient,
    common_job_parameters: Dict[str, Any],
) -> List[Dict]:
    organizations = get(api_session)
    load_organizations(
        neo4j_session, organizations, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)
    return organizations


@timeit
def get(
    api_session: AirbyteClient,
) -> List[Dict[str, Any]]:
    return api_session.get("/organizations")


@timeit
def load_organizations(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    logger.info("Loading %d Airbyte Organizations into Neo4j.", len(data))
    load(
        neo4j_session,
        AirbyteOrganizationSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(AirbyteOrganizationSchema(), common_job_parameters).run(
        neo4j_session
    )
