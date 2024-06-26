import logging
from typing import Dict
from typing import List

import neo4j
from falconpy.hosts import Hosts
from falconpy.oauth2 import OAuth2

from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_hosts(
    neo4j_session: neo4j.Session,
    update_tag: int,
    authorization: OAuth2,
) -> None:
    client = Hosts(auth_object=authorization)
    all_ids = get_host_ids(client)
    for ids in all_ids:
        host_data = get_hosts(client, ids)
        load_host_data(neo4j_session, host_data, update_tag)


def load_host_data(
    neo4j_session: neo4j.Session, data: List[Dict], update_tag: int,
) -> None:
    """
    Transform and load scan information
    """
    ingestion_cypher_query = """
    UNWIND $Hosts AS host
        MERGE (h:CrowdstrikeHost{id: host.device_id})
        ON CREATE SET h.cid = host.cid,
            h.cid = host.cid,
            h.instance_id = host.instance_id,
            h.firstseen = timestamp()
        SET h.status = host.status,
            h.hostname = host.hostname,
            h.machine_domain = host.machine_domain,
            h.crowdstrike_first_seen = host.first_seen,
            h.crowdstrike_last_seen = host.last_seen,
            h.local_ip = host.local_ip,
            h.external_ip = host.external_ip,
            h.cpu_signature = host.cpu_signature,
            h.bios_manufacturer = host.bios_manufacturer,
            h.bios_version = host.bios_version,
            h.mac_address = host.mac_address,
            h.os_version = host.os_version,
            h.os_build = host.os_build,
            h.platform_id = host.platform_id,
            h.platform_name = host.platform_name,
            h.service_provider = host.service_provider,
            h.service_provider_account_id = host.service_provider_account_id,
            h.agent_version = host.agent_version,
            h.system_manufacturer = host.system_manufacturer,
            h.system_product_name = host.system_product_name,
            h.product_type = host.product_type,
            h.product_type_desc = host.product_type_desc,
            h.provision_status = host.provision_status,
            h.reduced_functionality_mode = host.reduced_functionality_mode,
            h.kernel_version = host.kernel_version,
            h.major_version = host.major_version,
            h.minor_version = host.minor_version,
            h.tags = host.tags,
            h.modified_timestamp = host.modified_timestamp,
            h.lastupdated = $update_tag
    """
    logger.info(f"Loading {len(data)} crowdstrike hosts.")
    neo4j_session.run(
        ingestion_cypher_query,
        Hosts=data,
        update_tag=update_tag,
    )


def get_host_ids(client: Hosts, crowdstrikeapi_filter: str = '', crowdstrikeapi_limit: int = 5000) -> List[List[str]]:
    ids = []
    parameters = {"filter": crowdstrikeapi_filter, "limit": crowdstrikeapi_limit}
    response = client.QueryDevicesByFilter(parameters=parameters)
    body = response.get("body", {})
    resources = body.get("resources", [])
    if not resources:
        logger.warning("No host IDs in QueryDevicesByFilter.")
        return []
    ids.append(resources)
    offset = body.get("meta", {}).get("pagination", {}).get("offset")
    while offset:
        parameters["offset"] = offset
        response = client.QueryDevicesByFilter(parameters=parameters)
        body = response.get("body", {})
        resources = body.get("resources", [])
        if not resources:
            break
        ids.append(resources)
        offset = body.get("meta", {}).get("pagination", {}).get("offset")
    return ids


def get_hosts(client: Hosts, ids: List[str]) -> List[Dict]:
    response = client.GetDeviceDetails(ids=",".join(ids))
    body = response.get("body", {})
    return body.get("resources", [])
