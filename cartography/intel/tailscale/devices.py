import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.tailscale.device import TailscaleDeviceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: Dict[str, Any],
    org: str,
) -> List[Dict]:
    devices = get(
        api_session,
        common_job_parameters["BASE_URL"],
        org,
    )
    load_devices(
        neo4j_session,
        devices,
        org,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return devices


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    org: str,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    # CHANGEME: You have to handle pagination if needed
    req = api_session.get(
        f"{base_url}/tailnet/{org}/devices",
        timeout=_TIMEOUT,
    )
    req.raise_for_status()
    results = req.json()["devices"]
    return results


def load_devices(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    org: str,
    update_tag: int,
) -> None:
    logger.info(f"Loading {len(data)} Tailscale Users to the graph")
    load(
        neo4j_session,
        TailscaleDeviceSchema(),
        data,
        lastupdated=update_tag,
        org=org,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(TailscaleDeviceSchema(), common_job_parameters).run(
        neo4j_session
    )
