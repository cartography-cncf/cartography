import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from requests import Session

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.kandji.device import KandjiDeviceSchema
from cartography.models.kandji.tenant import KandjiTenantSchema
from cartography.util import timeit


logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)


@timeit
def get(kandji_base_uri: str, kandji_token: str) -> List[Dict[str, Any]]:
    api_endpoint = f"{kandji_base_uri}/api/v1/devices"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {kandji_token}',
    }

    session = Session()
    req = session.get(api_endpoint, headers=headers, timeout=_TIMEOUT)
    req.raise_for_status()
    return req.json()


@timeit
def transform(api_result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for device in api_result:
        n_device = device
        n_device['id'] = device['device_id']
        result.append(n_device)
    return result


@timeit
def load_devices(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
    data: List[Dict[str, Any]],
) -> None:

    tenant_id = common_job_parameters["TENANT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    load(
        neo4j_session,
        KandjiTenantSchema(),
        [{'id': tenant_id}],
        lastupdated=update_tag,
    )

    load(
        neo4j_session,
        KandjiDeviceSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    GraphJob.from_node_schema(KandjiDeviceSchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    kandji_base_uri: str,
    kandji_token: str,
    common_job_parameters: Dict[str, Any],
) -> None:
    devices = get(kandji_base_uri=kandji_base_uri, kandji_token=kandji_token)
    formatted_devices = transform(devices)
    load_devices(neo4j_session, common_job_parameters, formatted_devices)
    cleanup(neo4j_session, common_job_parameters)
