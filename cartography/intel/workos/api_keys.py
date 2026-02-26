import json
import logging
from typing import Any

import neo4j
from workos import WorkOSClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.workos.util import paginated_list
from cartography.models.workos.api_key import WorkOSAPIKeySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: WorkOSClient,
    organization_ids: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync WorkOS API Keys.

    :param neo4j_session: Neo4J session for database interface
    :param client: WorkOS API client
    :param organization_ids: List of organization IDs
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    client_id = common_job_parameters["WORKOS_CLIENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    api_keys = get(client, organization_ids)
    transformed_keys = transform(api_keys)
    load_api_keys(neo4j_session, transformed_keys, client_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(client: WorkOSClient, organization_ids: list[str]) -> list[dict[str, Any]]:
    """
    Fetch all API keys from WorkOS API.

    API keys are listed per organization via client.organizations.list_api_keys().

    :param client: WorkOS API client
    :param organization_ids: List of organization IDs
    :return: List of API key objects
    """
    logger.debug("Fetching WorkOS API keys")
    api_keys = []

    for org_id in organization_ids:
        try:
            org_keys = paginated_list(
                client.organizations.list_api_keys,
                organization_id=org_id,
            )
            api_keys.extend(org_keys)
        except Exception as e:
            logger.warning(f"Failed to fetch API keys for organization {org_id}: {e}")
            continue

    return api_keys


def transform(api_keys: list[Any]) -> list[dict[str, Any]]:
    """
    Transform API keys data for loading.

    :param api_keys: Raw API key objects from WorkOS
    :return: Transformed list of API key dicts
    """
    logger.debug(f"Transforming {len(api_keys)} WorkOS API keys")
    result = []

    for api_key in api_keys:
        key_dict = {
            "id": api_key.id,
            "name": api_key.name,
            "obfuscated_value": getattr(api_key, "obfuscated_value", None),
            "permissions": (
                json.dumps(api_key.permissions)
                if hasattr(api_key, "permissions") and api_key.permissions
                else None
            ),
            "created_at": api_key.created_at,
            "updated_at": api_key.updated_at,
            "last_used_at": getattr(api_key, "last_used_at", None),
        }

        if api_key.owner:
            if api_key.owner.type == "organization":
                key_dict["org_owner_id"] = api_key.owner.id
            elif api_key.owner.type == "user":
                key_dict["user_owner_id"] = api_key.owner.id
        result.append(key_dict)

    return result


@timeit
def load_api_keys(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    client_id: str,
    update_tag: int,
) -> None:
    """
    Load API keys into Neo4j.

    :param neo4j_session: Neo4J session for database interface
    :param data: List of API key dicts
    :param client_id: The WorkOS client ID
    :param update_tag: Update tag for tracking syncs
    :return: None
    """
    logger.info(f"Loading {len(data)} WorkOS API keys into Neo4j")
    load(
        neo4j_session,
        WorkOSAPIKeySchema(),
        data,
        lastupdated=update_tag,
        WORKOS_CLIENT_ID=client_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Cleanup old API keys.

    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    GraphJob.from_node_schema(
        WorkOSAPIKeySchema(),
        common_job_parameters,
    ).run(neo4j_session)
