import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from cloudflare import Cloudflare

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.cloudflare.member import CloudflareMemberSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: Cloudflare,
    common_job_parameters: Dict[str, Any],
    account_id: str,
) -> None:
    members = get(client, account_id)
    transformed_members = transform_members(members)
    load_members(
        neo4j_session,
        transformed_members,
        account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(client: Cloudflare, account_id: str) -> List[Dict[str, Any]]:
    return [
        member.to_dict()
        for member in client.accounts.members.list(account_id=account_id)
    ]


def load_members(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Cloudflare members into Neo4j.", len(data))
    load(
        neo4j_session,
        CloudflareMemberSchema(),
        data,
        lastupdated=update_tag,
        account_id=account_id,
    )


def transform_members(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for member in data:
        member["roles_ids"] = [role["id"] for role in member.get("roles", [])]
        member["policies_ids"] = [policy["id"] for policy in member.get("policies", [])]
        result.append(member)
    return result


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(CloudflareMemberSchema(), common_job_parameters).run(
        neo4j_session
    )
