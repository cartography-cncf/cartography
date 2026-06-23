from typing import Any
from typing import Dict
from typing import List

import neo4j
from cloudflare import Cloudflare

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.cloudflare.account import CloudflareAccountSchema
from cartography.util import timeit

# Documented maximum `per_page` for the Cloudflare /accounts endpoint.
MAX_ACCOUNTS_PER_PAGE = 50


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
    # The SDK auto-paginator increments `page` and stops only on an empty page,
    # which never terminates on /accounts (cloudflare/cloudflare-python#2584).
    # /accounts caps per_page at 50 and has no cursor, so fetch a single
    # max-size page and reconcile against total_count rather than iterating. If
    # more accounts exist than were returned, fail loudly instead of syncing a
    # partial set (correct whether or not `page` is honored).
    page = client.accounts.list(per_page=MAX_ACCOUNTS_PER_PAGE)
    accounts = [account.to_dict() for account in page.result or []]

    total_count = page.result_info.total_count
    if total_count is not None and total_count > len(accounts):
        raise RuntimeError(
            f"Cloudflare reports {total_count} accounts but only {len(accounts)} "
            f"were returned; /accounts caps per_page at {MAX_ACCOUNTS_PER_PAGE} "
            f"with no cursor pagination. Refusing to sync a partial account set."
        )
    return accounts


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
