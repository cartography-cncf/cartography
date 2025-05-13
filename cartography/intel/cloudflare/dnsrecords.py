import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import requests
from dateutil import parser as dt_parse
from requests import Session

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
    api_session: requests.Session,
    common_job_parameters: Dict[str, Any],
    zone_id,
) -> List[Dict]:
    dnsrecords = get(
        api_session,
        common_job_parameters["BASE_URL"],
        zone_id,
    )
    # CHANGEME: You can configure here a transform operation
    # formated_dnsrecords = transform(dnsrecords)
    load_dnsrecords(
        neo4j_session,
        dnsrecords,  # CHANGEME: replace with `formated_dnsrecords` if your added a transform step
        zone_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    zone_id,
) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    # CHANGEME: You have to handle pagination if needed
    req = api_session.get(
        "{base_url}/zones/{zone_id}/dns_records".format(
            base_url=base_url,
            zone_id=zone_id,
        ),
        timeout=_TIMEOUT,
    )
    req.raise_for_status()
    results = req.json()["result"]
    return results


def load_dnsrecords(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    zone_id,
    update_tag: int,
) -> None:
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
