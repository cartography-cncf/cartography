import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j

from cartography.client.core.tx import load
from cartography.intel.airbyte.util import AirbyteClient
from cartography.graph.job import GraphJob
from cartography.models.airbyte.user import AirbyteUserSchema
from cartography.util import timeit


logger = logging.getLogger(__name__)



@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: AirbyteClient,
    org_id: str,
    common_job_parameters: Dict[str, Any],
) -> None:
    users = get(api_session, org_id=org_id)
    # WIP: https://reference.airbyte.com/reference/listpermissions
    load_users(
        neo4j_session,
        users,
        org_id,
        common_job_parameters['UPDATE_TAG'])
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: AirbyteClient,
    org_id: str,
) -> List[Dict[str, Any]]:
    return api_session.get("/users", params={"organizationId": org_id})


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d AirbyteUserSchema into Neo4j.", len(data))
    load(
        neo4j_session,
        AirbyteUserSchema(),
        data,
        ORG_ID=org_id,
        lastupdated=update_tag,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    GraphJob.from_node_schema(
        AirbyteUserSchema(),
        common_job_parameters
    ).run(neo4j_session)
