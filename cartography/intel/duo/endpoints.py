import logging
from json import dumps
from typing import Any
from typing import Dict
from typing import List

import duo_client
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.duo.endpoint import DuoEndpointSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_duo_endpoints(
    client: duo_client.Admin,
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    '''
    Sync Duo Endpoints
    '''
    endpoints = _get_endpoints(client)
    transformed_endpoints = _transform_endpoints(endpoints)
    _load_endpoints(neo4j_session, transformed_endpoints, common_job_parameters)
    _cleanup_endpoints(neo4j_session, common_job_parameters)


@timeit
def _get_endpoints(client: duo_client.Admin) -> List[Dict[str, Any]]:
    '''
    Fetch all endpoint data
    https://duo.com/docs/adminapi#endpoints
    '''
    logger.info("Fetching Duo endpoints")
    return client.get_endpoints()


@timeit
def _transform_endpoints(endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    '''
    Reformat the data before loading
    '''
    logger.info(f'Transforming {len(endpoints)} duo endpoints')
    transformed_endpoints = []
    for endpoint in endpoints:
        transformed_endpoint = {
            'browsers': [dumps(browser) for browser in endpoint['browsers']],
            'computer_sid': endpoint['computer_sid'],
            'cpu_id': endpoint['cpu_id'],
            'device_id': endpoint['device_id'],
            'device_identifier': endpoint['device_identifier'],
            'device_identifier_type': endpoint['device_identifier_type'],
            'device_name': endpoint['device_name'],
            'device_udid': endpoint['device_udid'],
            'device_username': endpoint['device_username'],
            'device_username_type': endpoint['device_username_type'],
            'disk_encryption_status': endpoint['disk_encryption_status'],
            'domain_sid': endpoint['domain_sid'],
            'email': endpoint['email'],
            'epkey': endpoint['epkey'],
            'firewall_status': endpoint['firewall_status'],
            'hardware_uuid': endpoint['hardware_uuid'],
            'health_app_client_version': endpoint['health_app_client_version'],
            'health_data_last_collected': endpoint['health_data_last_collected'],
            'last_updated': endpoint['last_updated'],
            'machine_guid': endpoint['machine_guid'],
            'model': endpoint['model'],
            'os_build': endpoint['os_build'],
            'os_family': endpoint['os_family'],
            'os_version': endpoint['os_version'],
            'password_status': endpoint['password_status'],
            'security_agents': [dumps(agent) for agent in endpoint['security_agents']],
            'trusted_endpoint': endpoint['trusted_endpoint'],
            'type': endpoint['type'],
            'username': endpoint['username'],
        }
        transformed_endpoints.append(transformed_endpoint)
    return transformed_endpoints


@timeit
def _load_endpoints(
    neo4j_session: neo4j.Session,
    endpoints: List[Dict[str, Any]],
    common_job_parameters: Dict[str, Any],
) -> None:
    '''
    Load the endpoints into the database
    '''
    logger.info(f'Loading {len(endpoints)} duo endpoints')
    load(
        neo4j_session,
        DuoEndpointSchema(),
        endpoints,
        DUO_API_HOSTNAME=common_job_parameters['DUO_API_HOSTNAME'],
        lastupdated=common_job_parameters['UPDATE_TAG'],
    )


@timeit
def _cleanup_endpoints(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    '''
    Cleanup endpoints
    '''
    GraphJob.from_node_schema(DuoEndpointSchema(), common_job_parameters).run(neo4j_session)
