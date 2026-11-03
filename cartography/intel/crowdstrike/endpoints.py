import logging
from collections import defaultdict
from typing import Dict
from typing import Iterator
from typing import List

import neo4j
from falconpy.hosts import Hosts
from falconpy.oauth2 import OAuth2

from cartography.client.core.tx import load
from cartography.intel.crowdstrike.util import call_with_retries
from cartography.intel.crowdstrike.util import REQUEST_TIMEOUT_SECONDS
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
    client = Hosts(auth_object=authorization, timeout=REQUEST_TIMEOUT_SECONDS)
    for ids in get_host_ids(client):
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
) -> Iterator[List[str]]:
    """
    Yield host IDs one page at a time.

    Uses the scroll endpoint because QueryDevicesByFilter cannot page past an
    offset of 10,000, which silently capped larger tenants at 10,000 hosts.
    """
    parameters: dict[str, str | int] = {
        "filter": crowdstrikeapi_filter,
        "limit": crowdstrikeapi_limit,
    }
    seen = 0
    while True:
        body = call_with_retries(
            lambda: client.QueryDevicesByFilterScroll(parameters=parameters),
            "QueryDevicesByFilterScroll",
        )
        resources = body.get("resources") or []
        if not resources:
            if seen == 0:
                logger.warning("No host IDs in QueryDevicesByFilterScroll.")
            return
        seen += len(resources)
        yield resources
        pagination = body.get("meta", {}).get("pagination", {})
        offset = pagination.get("offset")
        total = pagination.get("total")
        if not offset or (total is not None and seen >= total):
            return
        parameters["offset"] = offset


def get_hosts(client: Hosts, ids: List[str]) -> List[Dict]:
    body = call_with_retries(
        lambda: client.GetDeviceDetails(ids=",".join(ids)), "GetDeviceDetails"
    )
    return body.get("resources", [])
