import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from digitalocean import Account
from digitalocean import Manager

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.digitalocean.account import DOAccountSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    manager: Manager,
    update_tag: int,
    common_job_parameters: dict,
) -> str:
    logger.info("Syncing Account")
    account = get_account(manager)
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
def get_account(manager: Manager) -> Account:
    return manager.get_account()


@timeit
def transform_account(account_res: Account) -> dict:
    return {
        "id": account_res.uuid,
        "uuid": account_res.uuid,
        "droplet_limit": account_res.droplet_limit,
        "floating_ip_limit": account_res.floating_ip_limit,
        "status": account_res.status,
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
