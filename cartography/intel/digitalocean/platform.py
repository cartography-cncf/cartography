import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from pydo import Client

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.digitalocean.account import DOAccountSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: Client,
    update_tag: int,
    common_job_parameters: dict,
) -> str:
    logger.info("Syncing Account")
    account = get_account(client)
    if not account:
        return ""
    account_transformed = transform_account(account)
    load_account(
        neo4j_session,
        [
            account_transformed,
        ],
        update_tag,
    )
    cleanup(neo4j_session, common_job_parameters)

    return account_transformed["id"]


@timeit
def get_account(client: Client) -> Dict[str, Any]:
    result = client.account.get()
    return result["account"]


@timeit
def transform_account(account_res: Dict[str, Any]) -> Dict[str, Any]:
    uuid = account_res.get("uuid")
    droplet_limit = account_res.get("droplet_limit")
    floating_ip_limit = account_res.get("floating_ip_limit")
    status = account_res.get("status")

    return {
        "id": uuid,
        "uuid": uuid,
        "droplet_limit": droplet_limit,
        "floating_ip_limit": floating_ip_limit,
        "status": status,
    }


@timeit
def load_account(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    load(neo4j_session, DOAccountSchema(), data, lastupdated=update_tag)


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    GraphJob.from_node_schema(DOAccountSchema(), common_job_parameters).run(
        neo4j_session,
    )
