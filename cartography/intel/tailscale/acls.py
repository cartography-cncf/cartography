import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.tailscale.utils import ACLParser
from cartography.intel.tailscale.utils import role_to_group
from cartography.models.tailscale.group import TailscaleGroupSchema
from cartography.models.tailscale.tag import TailscaleTagSchema
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
) -> None:
    raw_acl = get(
        api_session,
        common_job_parameters["BASE_URL"],
        org,
    )
    groups, tags = transform(raw_acl, users)
    load_groups(
        neo4j_session,
        groups,
        common_job_parameters["UPDATE_TAG"],
        org,
    )
    load_tags(
        neo4j_session,
        tags,
        org,
        common_job_parameters["UPDATE_TAG"],
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


def transform(
    raw_acl: str,
    users: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    transformed_groups: Dict[str, Dict[str, Any]] = {}
    transformed_tags: Dict[str, Dict[str, Any]] = {}

    parser = ACLParser(raw_acl)
    # Extract groups from the ACL
    for group in parser.get_groups():
        for dom in group["domain_members"]:
            for user in users:
                if user["loginName"].endswith(f"@{dom}"):
                    group["members"].append(user["loginName"])
        # Ensure domain members are unique
        group["domain_members"] = list(set(group["domain_members"]))
        transformed_groups[group["id"]] = group
    # Extract tags from the ACL
    for tag in parser.get_tags():
        for dom in tag["domain_owners"]:
            for user in users:
                if user["loginName"].endswith(f"@{dom}"):
                    tag["owners"].append(user["loginName"])
        # Ensure domain owners are unique
        tag["owners"] = list(set(tag["owners"]))
        transformed_tags[tag["id"]] = tag

    # Add autogroups based on user roles
    for user in users:
        for g in role_to_group(user["role"]):
            if g not in transformed_groups:
                transformed_groups[g] = {
                    "id": g,
                    "name": g.split(":")[-1],
                    "members": [],
                    "sub_groups": [],
                    "domain_members": [],
                }
            transformed_groups[g]["members"].append(user["loginName"])

    return list(transformed_groups.values()), list(transformed_tags.values())


@timeit
def load_groups(
    neo4j_session: neo4j.Session,
    groups: List[Dict[str, Any]],
    update_tag: str,
    org: str,
) -> None:
    logger.info(f"Loading {len(groups)} Tailscale Groups to the graph")
    load(neo4j_session, TailscaleGroupSchema(), groups, lastupdated=update_tag, org=org)


@timeit
def load_tags(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    org: str,
    update_tag: int,
) -> None:
    logger.info(f"Loading {len(data)} Tailscale Tags to the graph")
    load(
        neo4j_session,
        TailscaleTagSchema(),
        data,
        lastupdated=update_tag,
        org=org,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(TailscaleGroupSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(TailscaleTagSchema(), common_job_parameters).run(
        neo4j_session
    )
