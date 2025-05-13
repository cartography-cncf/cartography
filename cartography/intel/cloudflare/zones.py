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
from cartography.models.cloudflare.zone import CloudflareZoneSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: Dict[str, Any],
) -> List[Dict]:
    zones = get(
        api_session,
        common_job_parameters["BASE_URL"],
    )
    # CHANGEME: You can configure here a transform operation
    # formated_zones = transform(zones)
    load_zones(
        neo4j_session,
        zones,  # CHANGEME: replace with `formated_zones` if your added a transform step
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    params = {"page": 1, "per_page": 25}
    keep_running = True
    while keep_running:
        keep_running = False  # To avoid any infinite loop
        req = api_session.get(
            "{base_url}/zones".format(
                base_url=base_url,
            ),
            params=params,
            timeout=_TIMEOUT,
        )
        req.raise_for_status()
        sub_results = req.json()
        results.extend(sub_results)
        if len(sub_results) == 25:
            keep_running = True
        params["page"] += 1
    return results


def load_zones(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CloudflareZoneSchema(),
        data,
        lastupdated=update_tag,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(CloudflareZoneSchema(), common_job_parameters).run(
        neo4j_session
    )
