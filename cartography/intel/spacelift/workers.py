import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.spacelift.util import call_spacelift_api
from cartography.models.spacelift.worker import SpaceliftWorkerSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# GraphQL query to fetch workers nested under workerPools
# Note: Workers don't have a top-level query, they're nested under workerPools
# Note: Worker type doesn't have a 'name' field, only 'id' and 'status'
GET_WORKERS_QUERY = """
query {
    workerPools {
        id
        workers {
            id
            status
        }
    }
}
"""


@timeit
def get_workers(session: requests.Session, api_endpoint: str) -> list[dict[str, Any]]:
    """
    Fetch all Spacelift workers from the API.
    Workers are nested under workerPools, so we query workerPools and flatten the workers.
    """
    logger.info("Fetching Spacelift workers")

    response = call_spacelift_api(session, api_endpoint, GET_WORKERS_QUERY)
    worker_pools = response.get("data", {}).get("workerPools", [])

    # Flatten workers from all pools and add the pool ID to each worker
    all_workers = []
    for pool in worker_pools:
        pool_id = pool["id"]
        for worker in pool.get("workers", []):
            # Add the pool ID to each worker
            worker["workerPool"] = pool_id
            all_workers.append(worker)

    logger.info(
        f"Retrieved {len(all_workers)} Spacelift workers from {len(worker_pools)} worker pools"
    )
    return all_workers


def transform_workers(
    workers_data: list[dict[str, Any]], account_id: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for worker in workers_data:
        worker_id = worker["id"]

        transformed_worker = {
            "id": worker_id,
            "name": worker_id,  # Use ID as name since Worker type doesn't have a name field
            "status": worker.get("status"),
            "worker_pool_id": worker.get("workerPool"),
            "spacelift_account_id": account_id,
        }

        result.append(transformed_worker)

    logger.info(f"Transformed {len(result)} workers")
    return result


def load_workers(
    neo4j_session: neo4j.Session,
    workers_data: list[dict[str, Any]],
    update_tag: int,
    account_id: str,
) -> None:

    load(
        neo4j_session,
        SpaceliftWorkerSchema(),
        workers_data,
        lastupdated=update_tag,
        spacelift_account_id=account_id,
    )

    logger.info(f"Loaded {len(workers_data)} Spacelift workers")


@timeit
def cleanup_workers(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:

    logger.debug("Running SpaceliftWorker cleanup job")
    GraphJob.from_node_schema(SpaceliftWorkerSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_workers(
    neo4j_session: neo4j.Session,
    spacelift_session: requests.Session,
    api_endpoint: str,
    account_id: str,
    common_job_parameters: dict[str, Any],
) -> None:

    workers_raw_data = get_workers(spacelift_session, api_endpoint)
    transformed_workers = transform_workers(workers_raw_data, account_id)
    load_workers(
        neo4j_session,
        transformed_workers,
        common_job_parameters["UPDATE_TAG"],
        account_id,
    )
    cleanup_workers(neo4j_session, common_job_parameters)

    logger.info(f"Synced {len(transformed_workers)} Spacelift workers")
