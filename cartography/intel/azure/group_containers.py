import logging
from typing import Any

import neo4j
from azure.core.exceptions import ClientAuthenticationError
from azure.core.exceptions import HttpResponseError
from azure.mgmt.containerinstance import ContainerInstanceManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.azure.util.tag import transform_tags
from cartography.models.azure.group_container import AzureGroupContainerSchema
from cartography.models.azure.tags.group_container_tag import (
    AzureGroupContainerTagsSchema,
)
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


@timeit
def get_container_groups(credentials: Credentials, subscription_id: str) -> list[dict]:
    try:
        client = ContainerInstanceManagementClient(
            credentials.credential, subscription_id
        )
        return [cg.as_dict() for cg in client.container_groups.list()]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(
            f"Failed to get container groups for subscription {subscription_id}: {str(e)}"
        )
        return []


def transform_group_containers(container_groups: list[dict]) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for group in container_groups:
        subnet_ids: list[str] = []
        # Azure SDK as_dict() returns flat structure (not nested under "properties").
        # Use `or []` chain rather than dict.get(..., default) so an explicit
        # null in the API response does not crash iteration.
        for subnet_ref in (
            group.get("subnet_ids")
            or group.get("properties", {}).get("subnet_ids")
            or []
        ):
            subnet_id = subnet_ref.get("id")
            if subnet_id:
                subnet_ids.append(subnet_id)

        transformed.append(
            {
                "id": group.get("id"),
                "name": group.get("name"),
                "location": group.get("location"),
                "type": group.get("type"),
                "provisioning_state": group.get(
                    "provisioning_state",
                    group.get("properties", {}).get("provisioning_state"),
                ),
                "ip_address": (
                    group.get("ip_address")
                    or group.get("properties", {}).get("ip_address")
                    or {}
                ).get("ip"),
                "ip_address_type": (
                    group.get("ip_address")
                    or group.get("properties", {}).get("ip_address")
                    or {}
                ).get("type"),
                "os_type": group.get(
                    "os_type", group.get("properties", {}).get("os_type")
                ),
                "tags": group.get("tags"),
                "SUBNET_IDS": subnet_ids,
            },
        )
    return transformed


@timeit
def load_group_containers(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureGroupContainerSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_group_container_tags(
    neo4j_session: neo4j.Session,
    subscription_id: str,
    groups: list[dict],
    update_tag: int,
) -> None:
    tags = transform_tags(groups, subscription_id)
    load(
        neo4j_session,
        AzureGroupContainerTagsSchema(),
        tags,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def cleanup_group_containers(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(AzureGroupContainerSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_group_container_tags(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(
        AzureGroupContainerTagsSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync_group_containers(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(f"Syncing Azure Group Containers for subscription {subscription_id}.")
    raw_groups = get_container_groups(credentials, subscription_id)
    transformed = transform_group_containers(raw_groups)
    load_group_containers(neo4j_session, transformed, subscription_id, update_tag)
    load_group_container_tags(neo4j_session, subscription_id, transformed, update_tag)
    cleanup_group_containers(neo4j_session, common_job_parameters)
    cleanup_group_container_tags(neo4j_session, common_job_parameters)
