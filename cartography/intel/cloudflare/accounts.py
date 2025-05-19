import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from cloudflare import Cloudflare

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.cloudflare.account import CloudflareAccountSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: Cloudflare,
    common_job_parameters: Dict[str, Any],
) -> List[Dict]:
    accounts = get(client)
    load_accounts(
        neo4j_session,
        accounts,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return accounts


@timeit
def get(client: Cloudflare) -> List[Dict[str, Any]]:
    return [account.to_dict() for account in client.accounts.list()]


def load_accounts(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    logger.info("Loading %d Cloudflare accounts into Neo4j.", len(data))
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
