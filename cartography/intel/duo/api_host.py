import logging
from typing import Any
from typing import Dict

import neo4j

from cartography.client.core.tx import load
from cartography.models.duo.api_host import DuoApiHostSchema
from cartography.util import timeit


logger = logging.getLogger(__name__)


@timeit
def sync_duo_api_host(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    '''
    Add the DuoApiHost subresource
    '''
    _load_api_host(neo4j_session, common_job_parameters)


@timeit
def _load_api_host(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    '''
    Load the host node into the graph
    '''
    data = [
        {
            'id': common_job_parameters['DUO_API_HOSTNAME'],
        },
    ]
    load(
        neo4j_session,
        DuoApiHostSchema(),
        data,
        lastupdated=common_job_parameters['UPDATE_TAG'],
    )
