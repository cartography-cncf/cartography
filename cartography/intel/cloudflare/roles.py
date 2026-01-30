import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from cloudflare import Cloudflare

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.cloudflare.role import CloudflareRoleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: Cloudflare,
    common_job_parameters: Dict[str, Any],
    account_id: str,
) -> None:
    roles = get(client, account_id)
    load_roles(
        neo4j_session,
        roles,
        account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    client: Cloudflare,
    account_id: str,
) -> List[Dict[str, Any]]:
    return [
        role.to_dict() for role in client.accounts.roles.list(account_id=account_id)
    ]


def load_roles(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Cloudflare roles into Neo4j.", len(data))
    load(
        neo4j_session,
        CloudflareRoleSchema(),
        data,
        lastupdated=update_tag,
        account_id=account_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(CloudflareRoleSchema(), common_job_parameters).run(
        neo4j_session
    )
