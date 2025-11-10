import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.spacelift.util import call_spacelift_api
from cartography.models.spacelift.stack import SpaceliftStackSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# GraphQL query to fetch all stacks (direct array, no pagination)
GET_STACKS_QUERY = """
query {
    stacks {
        id
        name
        description
        state
        administrative
        repository
        branch
        projectRoot
        space
    }
}
"""


@timeit
def get_stacks(session: requests.Session, api_endpoint: str) -> list[dict[str, Any]]:
    logger.info("Fetching Spacelift stacks")

    response = call_spacelift_api(session, api_endpoint, GET_STACKS_QUERY)
    stacks_data = response.get("data", {}).get("stacks", [])

    logger.info(f"Retrieved {len(stacks_data)} Spacelift stacks")
    return stacks_data


def transform_stacks(
    stacks_data: list[dict[str, Any]], account_id: str
) -> list[dict[str, Any]]:

    result: list[dict[str, Any]] = []

    for stack in stacks_data:
        transformed_stack = {
            "id": stack["id"],
            "name": stack.get("name"),
            "description": stack.get("description"),
            "state": stack.get("state"),
            "administrative": stack.get("administrative"),
            "repository": stack.get("repository"),
            "branch": stack.get("branch"),
            "project_root": stack.get("projectRoot"),
            "space_id": stack.get("space"),
            "spacelift_account_id": account_id,
        }

        result.append(transformed_stack)

    logger.info(f"Transformed {len(result)} stacks")
    return result


def load_stacks(
    neo4j_session: neo4j.Session,
    stacks_data: list[dict[str, Any]],
    update_tag: int,
    account_id: str,
) -> None:

    load(
        neo4j_session,
        SpaceliftStackSchema(),
        stacks_data,
        lastupdated=update_tag,
        spacelift_account_id=account_id,
    )

    logger.info(f"Loaded {len(stacks_data)} Spacelift stacks")


@timeit
def cleanup_stacks(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:

    logger.debug("Running SpaceliftStack cleanup job")
    GraphJob.from_node_schema(SpaceliftStackSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_stacks(
    neo4j_session: neo4j.Session,
    spacelift_session: requests.Session,
    api_endpoint: str,
    account_id: str,
    common_job_parameters: dict[str, Any],
) -> None:

    stacks_raw_data = get_stacks(spacelift_session, api_endpoint)
    transformed_stacks = transform_stacks(stacks_raw_data, account_id)
    load_stacks(
        neo4j_session,
        transformed_stacks,
        common_job_parameters["UPDATE_TAG"],
        account_id,
    )
    cleanup_stacks(neo4j_session, common_job_parameters)

    logger.info(f"Synced {len(transformed_stacks)} Spacelift stacks")
