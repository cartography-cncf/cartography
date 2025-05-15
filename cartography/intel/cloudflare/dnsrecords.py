import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from cloudflare import Cloudflare

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.cloudflare.dnsrecord import CloudflareDNSRecordSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: Cloudflare,
    common_job_parameters: Dict[str, Any],
    zone_id: str,
) -> None:
    dnsrecords = get(client, zone_id)
    load_dnsrecords(
        neo4j_session,
        dnsrecords,
        zone_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(client: Cloudflare, zone_id: str) -> List[Dict[str, Any]]:
    return [
        dnsrecord.to_dict() for dnsrecord in client.dns.records.list(zone_id=zone_id)
    ]


def load_dnsrecords(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    zone_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Cloudflare DNSRecords into Neo4j.", len(data))
    load(
        neo4j_session,
        CloudflareDNSRecordSchema(),
        data,
        lastupdated=update_tag,
        zone_id=zone_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(CloudflareDNSRecordSchema(), common_job_parameters).run(
        neo4j_session
    )
