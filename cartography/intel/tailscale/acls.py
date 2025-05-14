import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.tailscale.utils import ACLParser
from cartography.models.tailscale.group import TailscaleGroupSchema
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
    users: List[Dict[str, Any]],
) -> List[Dict]:
    raw_acl = get(
        api_session,
        common_job_parameters["BASE_URL"],
        org,
    )
    groups = transform(raw_acl, users)
    load_groups(
        neo4j_session,
        groups,
        common_job_parameters["UPDATE_TAG"],
        org,
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    org: str,
) -> str:
    req = api_session.get(
        f"{base_url}/tailnet/{org}/acl",
        timeout=_TIMEOUT,
    )
    req.raise_for_status()
    return req.text


@timeit
def transform(
    raw_acl: str,
    users: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    transformed_groups: List[Dict[str, Any]] = []

    parser = ACLParser(raw_acl)
    # Extract groups
    for group in parser.get_groups():
        for dom in group["domain_members"]:
            for user in users:
                if user["loginName"].endswith(f"@{dom}"):
                    group["members"].append(user["loginName"])
        # Ensure domain members are unique
        group["domain_members"] = list(set(group["domain_members"]))
        transformed_groups.append(group)

    return transformed_groups


@timeit
def load_groups(
    neo4j_session: neo4j.Session,
    groups: List[Dict[str, Any]],
    update_tag: str,
    org: str,
) -> None:
    logger.info(f"Loading {len(groups)} Tailscale Groups to the graph")
    load(neo4j_session, TailscaleGroupSchema(), groups, lastupdated=update_tag, org=org)


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(TailscaleGroupSchema(), common_job_parameters).run(
        neo4j_session
    )
