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
def get_account(api_endpoint: str) -> dict:

    logger.info("Extracting Spacelift account information from API endpoint")

    # Parse URL to extract subdomain (account ID)
    parsed = urlparse(api_endpoint)
    hostname = parsed.hostname or ""

    # Extract subdomain (everything before .app.spacelift.io)
    # Example: subimage.app.spacelift.io -> subimage
    account_id = hostname.split(".")[0] if hostname else ""

    if not account_id:
        raise ValueError(
            f"Could not extract account ID from API endpoint: {api_endpoint}"
        )

    logger.info(f"Extracted account ID: {account_id}")

    return {
        "id": account_id,
        "name": account_id,
    }


def transform_account(account_data: dict) -> dict:
    return {
        "id": account_data["id"],
        "account_id": account_data["id"],
        "name": account_data.get("name"),
    }


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

    logger.info(f"Loaded Spacelift account: {account_data.get('name')}")


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

    account_raw_data = get_account(api_endpoint)

    transformed_account = transform_account(account_raw_data)

    load_account(
        neo4j_session, transformed_account, common_job_parameters["UPDATE_TAG"]
    )

    cleanup_account(neo4j_session, common_job_parameters)

    account_id = transformed_account["account_id"]
    logger.info(f"Synced Spacelift account: {account_id}")
    return account_id
