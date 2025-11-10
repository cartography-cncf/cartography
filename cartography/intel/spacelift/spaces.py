import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.spacelift.util import call_spacelift_api
from cartography.models.spacelift.space import SpaceliftSpaceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# GraphQL query to fetch all spaces (direct array, no pagination)
GET_SPACES_QUERY = """
query {
    spaces {
        id
        name
        description
        parentSpace
    }
}
"""


@timeit
def get_spaces(session: requests.Session, api_endpoint: str) -> list[dict[str, Any]]:
    logger.info("Fetching Spacelift spaces")

    response = call_spacelift_api(session, api_endpoint, GET_SPACES_QUERY)
    spaces_data = response.get("data", {}).get("spaces", [])

    logger.info(f"Retrieved {len(spaces_data)} Spacelift spaces")
    return spaces_data


def transform_spaces(
    spaces_data: list[dict[str, Any]], account_id: str
) -> list[dict[str, Any]]:

    result: list[dict[str, Any]] = []

    for space in spaces_data:
        parent_space = space.get("parentSpace")
        # A space is root if it has no parent space
        is_root = parent_space is None

        transformed_space = {
            "id": space["id"],
            "name": space.get("name"),
            "description": space.get("description"),
            "is_root": is_root,
            "spacelift_account_id": account_id,
            "parent_spacelift_account_id": account_id if is_root else None,
            "parent_space_id": parent_space,
        }

        result.append(transformed_space)

    logger.info(f"Transformed {len(result)} spaces")
    return result


def load_spaces(
    neo4j_session: neo4j.Session,
    spaces_data: list[dict[str, Any]],
    update_tag: int,
    account_id: str,
) -> None:
    load(
        neo4j_session,
        SpaceliftSpaceSchema(),
        spaces_data,
        lastupdated=update_tag,
        spacelift_account_id=account_id,
    )

    logger.info(f"Loaded {len(spaces_data)} Spacelift spaces")


@timeit
def cleanup_spaces(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.debug("Running SpaceliftSpace cleanup job")
    GraphJob.from_node_schema(SpaceliftSpaceSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_spaces(
    neo4j_session: neo4j.Session,
    spacelift_session: requests.Session,
    api_endpoint: str,
    account_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    spaces_raw_data = get_spaces(spacelift_session, api_endpoint)
    transformed_spaces = transform_spaces(spaces_raw_data, account_id)
    load_spaces(
        neo4j_session,
        transformed_spaces,
        common_job_parameters["UPDATE_TAG"],
        account_id,
    )
    cleanup_spaces(neo4j_session, common_job_parameters)

    logger.info(f"Synced {len(transformed_spaces)} Spacelift spaces")
