import logging
from typing import Any
from urllib.parse import urlparse

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.spacelift.spaceliftaccount import SpaceliftAccountSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_account(api_endpoint: str) -> str:
    # Parse URL to extract subdomain (account ID)
    parsed = urlparse(api_endpoint)
    hostname = parsed.hostname or ""
    # Extract subdomain (everything before .app.spacelift.io)
    account_id = hostname.split(".")[0] if hostname else ""

    return account_id


def load_account(
    neo4j_session: neo4j.Session,
    account_data: dict,
    update_tag: int,
) -> None:

    load(
        neo4j_session,
        SpaceliftAccountSchema(),
        [account_data],
        lastupdated=update_tag,
    )

    logger.info(f"Loaded Spacelift account: {account_data['id']}")


@timeit
def cleanup_account(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:

    logger.debug("Running SpaceliftAccount cleanup job")
    GraphJob.from_node_schema(SpaceliftAccountSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_account(
    neo4j_session: neo4j.Session,
    api_endpoint: str,
    common_job_parameters: dict[str, Any],
) -> str:

    account_id = get_account(api_endpoint)

    # Transform account data (all fields are just spacelift_account_id)
    account_data = {
        "id": account_id,
        "spacelift_account_id": account_id,
        "name": account_id,
    }

    load_account(neo4j_session, account_data, common_job_parameters["UPDATE_TAG"])
    cleanup_account(neo4j_session, common_job_parameters)
    logger.info(f"Synced Spacelift account: {account_id}")
    return account_id
