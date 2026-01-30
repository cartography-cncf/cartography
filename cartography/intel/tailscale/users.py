import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.tailscale.user import TailscaleUserSchema
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
    users = get(
        api_session,
        common_job_parameters["BASE_URL"],
        org,
    )
    load_users(
        neo4j_session,
        users,
        org,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return users


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    org: str,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    req = api_session.get(
        f"{base_url}/tailnet/{org}/users",
        timeout=_TIMEOUT,
    )
    req.raise_for_status()
    results = req.json()["users"]
    return results


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    org: str,
    update_tag: int,
) -> None:
    logger.info(f"Loading {len(data)} Tailscale Users to the graph")
    load(
        neo4j_session,
        TailscaleUserSchema(),
        data,
        lastupdated=update_tag,
        org=org,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(TailscaleUserSchema(), common_job_parameters).run(
        neo4j_session
    )
