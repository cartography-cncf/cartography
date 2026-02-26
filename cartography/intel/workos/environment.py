import logging
from typing import Any
from typing import Dict

import neo4j

from cartography.client.core.tx import load
from cartography.models.workos.environment import WorkOSEnvironmentSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    """
    Sync WorkOS Environment node. This is a local-only node created from config.

    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    client_id = common_job_parameters["WORKOS_CLIENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    logger.info(f"Syncing WorkOS Environment: {client_id}")

    load(
        neo4j_session,
        WorkOSEnvironmentSchema(),
        [{"id": client_id}],
        lastupdated=update_tag,
    )
