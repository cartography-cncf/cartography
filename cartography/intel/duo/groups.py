import logging
from typing import Any
from typing import Dict
from typing import List

import duo_client
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.duo.group import DuoGroupSchema
from cartography.util import timeit


logger = logging.getLogger(__name__)


@timeit
def sync_duo_groups(
    client: duo_client.Admin,
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    '''
    Sync Duo groups
    '''
    groups = _get_groups(client)
    _load_groups(neo4j_session, groups, common_job_parameters)
    _cleanup_groups(neo4j_session, common_job_parameters)


@timeit
def _get_groups(client: duo_client.Admin) -> List[Dict[str, Any]]:
    '''
    Fetch all group data
    https://duo.com/docs/adminapi#users
    '''
    logger.info("Fetching Duo groups")
    return client.get_groups()


@timeit
def _load_groups(
    neo4j_session: neo4j.Session,
    groups: List[Dict[str, Any]],
    common_job_parameters: Dict[str, Any],
) -> None:
    '''
    Load the groups into the graph
    '''
    logger.info(f'Loading {len(groups)} duo groups')
    load(
        neo4j_session,
        DuoGroupSchema(),
        groups,
        DUO_API_HOSTNAME=common_job_parameters['DUO_API_HOSTNAME'],
        lastupdated=common_job_parameters['UPDATE_TAG'],
    )


@timeit
def _cleanup_groups(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    '''
    Cleanup endpoints
    '''
    GraphJob.from_node_schema(DuoGroupSchema(), common_job_parameters).run(neo4j_session)
