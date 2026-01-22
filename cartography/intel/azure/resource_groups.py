import logging
from typing import Any

import neo4j
from azure.core.exceptions import ClientAuthenticationError
from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import ResourceManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.azure.util.tag import transform_tags
from cartography.models.azure.resource_groups import AzureResourceGroupSchema
from cartography.models.azure.tags.resource_group_tag import (
    AzureResourceGroupTagsSchema,
)
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


@timeit
def get_resource_groups(credentials: Credentials, subscription_id: str) -> list[dict]:
    try:
        client = ResourceManagementClient(credentials.credential, subscription_id)
        return [rg.as_dict() for rg in client.resource_groups.list()]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(
            f"Failed to get Resource Groups for subscription {subscription_id}: {str(e)}"
        )
        return []


@timeit
def transform_resource_groups(resource_groups_response: list[dict]) -> list[dict]:
    transformed_groups: list[dict[str, Any]] = []
    for rg in resource_groups_response:
        transformed_group = {
            "id": rg.get("id"),
            "name": rg.get("name"),
            "location": rg.get("location"),
            "provisioning_state": rg.get("properties", {}).get("provisioning_state"),
            "tags": rg.get("tags"),
        }
        transformed_groups.append(transformed_group)
    return transformed_groups


@timeit
def load_resource_groups(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureResourceGroupSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_resource_group_tags(
    neo4j_session: neo4j.Session,
    subscription_id: str,
    resource_groups: list[dict],
    update_tag: int,
) -> None:
    """
    Loads tags for Resource Groups.
    """
    tags = transform_tags(resource_groups, subscription_id)
    load(
        neo4j_session,
        AzureResourceGroupTagsSchema(),
        tags,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def cleanup_resource_groups(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(AzureResourceGroupSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_resource_group_tags(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    """
    Runs cleanup job for Azure Resource Group tags.
    """
    GraphJob.from_node_schema(
        AzureResourceGroupTagsSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(f"Syncing Azure Resource Groups for subscription {subscription_id}.")
    raw_groups = get_resource_groups(credentials, subscription_id)
    transformed_groups = transform_resource_groups(raw_groups)
    load_resource_groups(neo4j_session, transformed_groups, subscription_id, update_tag)
    load_resource_group_tags(
        neo4j_session, subscription_id, transformed_groups, update_tag
    )
    cleanup_resource_groups(neo4j_session, common_job_parameters)
    cleanup_resource_group_tags(neo4j_session, common_job_parameters)
