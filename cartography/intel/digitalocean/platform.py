import logging

import neo4j
from digitalocean import Account

from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    account: Account,
    digitalocean_update_tag: int,
    common_job_parameters: dict,
) -> None:
    sync_account(neo4j_session, account, digitalocean_update_tag, common_job_parameters)


@timeit
def sync_account(
    neo4j_session: neo4j.Session,
    account: Account,
    digitalocean_update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info("Syncing Account")
    account_transformed = transform_account(account)
    load_account(neo4j_session, account_transformed, digitalocean_update_tag)
    return


@timeit
def transform_account(account_res: Account) -> dict:
    account = {
        "id": account_res.uuid,
        "uuid": account_res.uuid,
        "droplet_limit": account_res.droplet_limit,
        "floating_ip_limit": account_res.floating_ip_limit,
        "status": account_res.status,
    }
    return account


@timeit
def load_account(
    neo4j_session: neo4j.Session,
    account: dict,
    digitalocean_update_tag: int,
) -> None:
    query = """
            MERGE (a:DOAccount{id:$AccountId})
            ON CREATE SET a.firstseen = timestamp()
            SET a.uuid = $Uuid,
            a.droplet_limit = $DropletLimit,
            a.floating_ip_limit = $FloatingIpLimit,
            a.status = $Status,
            a.lastupdated = $digitalocean_update_tag
            """
    neo4j_session.run(
        query,
        AccountId=account["id"],
        Uuid=account["uuid"],
        DropletLimit=account["droplet_limit"],
        FloatingIpLimit=account["floating_ip_limit"],
        Status=account["status"],
        digitalocean_update_tag=digitalocean_update_tag,
    )
    return
