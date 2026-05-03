import logging
from collections import defaultdict
from typing import Dict
from typing import List

import neo4j
from falconpy.hosts import Hosts
from falconpy.oauth2 import OAuth2

from cartography.client.core.tx import load
from cartography.models.crowdstrike.hosts import CrowdstrikeHostSchema
from cartography.models.crowdstrike.tenant import CrowdstrikeTenantSchema
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


@timeit
def load_host_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Load Crowdstrike host data into Neo4j, grouping by CID so each batch is
    scoped to its tenant.
    """
    hosts_by_cid: dict[str, list[Dict]] = defaultdict(list)
    missing_cid: list[str] = []
    for host in data:
        cid = host.get("cid")
        if not cid:
            missing_cid.append(host.get("device_id") or "<unknown>")
            continue
        hosts_by_cid[cid].append(host)
    if missing_cid:
        raise ValueError(
            "CrowdStrike returned host records with no `cid`; refusing to load "
            f"because the tenant scope cannot be resolved. Affected device_ids: {missing_cid}"
        )
    if not hosts_by_cid:
        return
    load(
        neo4j_session,
        CrowdstrikeTenantSchema(),
        [{"id": cid} for cid in hosts_by_cid],
        lastupdated=update_tag,
    )
    for cid, hosts in hosts_by_cid.items():
        load(
            neo4j_session,
            CrowdstrikeHostSchema(),
            hosts,
            lastupdated=update_tag,
            CID=cid,
        )


def get_host_ids(
    client: Hosts,
    crowdstrikeapi_filter: str = "",
    crowdstrikeapi_limit: int = 5000,
) -> List[List[str]]:
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
