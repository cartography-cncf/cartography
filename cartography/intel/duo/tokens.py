import json
import logging
from typing import Any
from typing import Dict
from typing import List

import duo_client
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.duo.token import DuoTokenSchema as Schema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    client: duo_client.Admin,
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    '''
    Sync
    '''
    data = _get(client)
    transformed_data = _transform(data)
    _load(neo4j_session, transformed_data, common_job_parameters)
    _cleanup(neo4j_session, common_job_parameters)


@timeit
def _get(client: duo_client.Admin) -> List[Dict[str, Any]]:
    '''
    Fetch all data
    https://duo.com/docs/adminapi#endpoints
    '''
    logger.info(f'Fetching data for {Schema.label}')
    return client.get_tokens()


@timeit
def _transform(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    '''
    Reformat the data before loading
    '''
    logger.info(f'Transforming {len(data)} items for {Schema.label}')
    transformed_data = []
    for datum in data:
        transformed_datum = {
            'admins': json.dumps(datum['admins']),
            'serial': datum['serial'],
            'token_id': datum['token_id'],
            'totp_step': datum['totp_step'],
            'type': datum['type'],
        }
        transformed_data.append(transformed_datum)
        for user in datum['users']:
            match_datum = {
                **transformed_datum,
                'user_id': user['user_id'],
            }
            transformed_data.append(match_datum)
    return transformed_data


@timeit
def _load(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    common_job_parameters: Dict[str, Any],
) -> None:
    '''
    Load the data into the database
    '''
    logger.info(f'Loading {len(data)} items for {Schema.label}')
    load(
        neo4j_session,
        Schema(),
        data,
        DUO_API_HOSTNAME=common_job_parameters['DUO_API_HOSTNAME'],
        lastupdated=common_job_parameters['UPDATE_TAG'],
    )


@timeit
def _cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    '''
    Cleanup nodes
    '''
    GraphJob.from_node_schema(Schema(), common_job_parameters).run(neo4j_session)
