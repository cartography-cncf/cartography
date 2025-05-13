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
from cartography.models.cloudflare.account import CloudflareAccountSchema
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
    accounts = get(
        api_session,
        common_job_parameters["BASE_URL"],
    )
    # CHANGEME: You can configure here a transform operation
    # formated_accounts = transform(accounts)
    load_accounts(
        neo4j_session,
        accounts,  # CHANGEME: replace with `formated_accounts` if your added a transform step
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    # CHANGEME: You have to handle pagination if needed
    req = api_session.get(
        "{base_url}/accounts".format(
            base_url=base_url,
        ),
        timeout=_TIMEOUT,
    )
    req.raise_for_status()
    results = req.json()["result"]
    return results


def load_accounts(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CloudflareAccountSchema(),
        data,
        lastupdated=update_tag,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(CloudflareAccountSchema(), common_job_parameters).run(
        neo4j_session
    )
