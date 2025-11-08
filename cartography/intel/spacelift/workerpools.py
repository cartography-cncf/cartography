import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.spacelift.util import call_spacelift_api
from cartography.models.spacelift.workerpool import SpaceliftWorkerPoolSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# GraphQL query to fetch all worker pools (direct array, no pagination)
GET_WORKER_POOLS_QUERY = """
query {
    workerPools {
        id
        name
        description
        space
    }
}
"""


@timeit
def get_worker_pools(
    session: requests.Session, api_endpoint: str
) -> list[dict[str, Any]]:

    logger.info("Fetching Spacelift worker pools")

    response = call_spacelift_api(session, api_endpoint, GET_WORKER_POOLS_QUERY)
    worker_pools_data = response.get("data", {}).get("workerPools", [])

    logger.info(f"Retrieved {len(worker_pools_data)} Spacelift worker pools")
    return worker_pools_data


def transform_worker_pools(
    worker_pools_data: list[dict[str, Any]], account_id: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for pool in worker_pools_data:
        transformed_pool = {
            "id": pool["id"],
            "name": pool.get("name"),
            "description": pool.get("description"),
            "pool_type": None,  # WorkerPool type doesn't have a 'type' field in the API
            "space_id": pool.get("space"),
            "spacelift_account_id": account_id,
        }

        result.append(transformed_pool)

    logger.info(f"Transformed {len(result)} worker pools")
    return result


def load_worker_pools(
    neo4j_session: neo4j.Session,
    worker_pools_data: list[dict[str, Any]],
    update_tag: int,
    account_id: str,
) -> None:
    """
    Load Spacelift worker pools data into Neo4j using the data model.
    """
    load(
        neo4j_session,
        SpaceliftWorkerPoolSchema(),
        worker_pools_data,
        lastupdated=update_tag,
        spacelift_account_id=account_id,
    )

    logger.info(f"Loaded {len(worker_pools_data)} Spacelift worker pools")


@timeit
def cleanup_worker_pools(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove stale Spacelift worker pool data from Neo4j.
    """
    logger.debug("Running SpaceliftWorkerPool cleanup job")
    GraphJob.from_node_schema(SpaceliftWorkerPoolSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_worker_pools(
    neo4j_session: neo4j.Session,
    spacelift_session: requests.Session,
    api_endpoint: str,
    account_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Spacelift worker pools data to Neo4j.

    :param neo4j_session: Neo4j session
    :param spacelift_session: Authenticated requests session for Spacelift API
    :param api_endpoint: Spacelift GraphQL API endpoint
    :param account_id: The Spacelift account ID
    :param common_job_parameters: Common job parameters containing UPDATE_TAG
    """
    # 1. GET - Fetch data from Spacelift API
    worker_pools_raw_data = get_worker_pools(spacelift_session, api_endpoint)

    # 2. TRANSFORM - Shape data for ingestion
    transformed_worker_pools = transform_worker_pools(worker_pools_raw_data, account_id)

    # 3. LOAD - Ingest to Neo4j using data model
    load_worker_pools(
        neo4j_session,
        transformed_worker_pools,
        common_job_parameters["UPDATE_TAG"],
        account_id,
    )

    # 4. CLEANUP - Remove stale data
    cleanup_worker_pools(neo4j_session, common_job_parameters)

    logger.info(f"Synced {len(transformed_worker_pools)} Spacelift worker pools")
