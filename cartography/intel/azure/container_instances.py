import logging
from typing import Any

import neo4j
from azure.core.exceptions import ClientAuthenticationError
from azure.core.exceptions import HttpResponseError
from azure.mgmt.containerinstance import ContainerInstanceManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.container_instance import AzureContainerInstanceSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


@timeit
def get_container_instances(
    credentials: Credentials, subscription_id: str
) -> list[dict]:
    try:
        client = ContainerInstanceManagementClient(
            credentials.credential, subscription_id
        )
        # NOTE: Azure Container Instances are called "Container Groups" in the SDK
        return [cg.as_dict() for cg in client.container_groups.list()]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(
            f"Failed to get Container Instances for subscription {subscription_id}: {str(e)}"
        )
        return []


def transform_container_instances(container_groups: list[dict]) -> list[dict]:
    transformed_instances: list[dict[str, Any]] = []
    for group in container_groups:
        transformed_instance = {
            "id": group.get("id"),
            "name": group.get("name"),
            "location": group.get("location"),
            "type": group.get("type"),
            "provisioning_state": group.get("properties", {}).get("provisioning_state"),
            "ip_address": ((group.get("properties") or {}).get("ip_address") or {}).get(
                "ip"
            ),
            "os_type": group.get("properties", {}).get("os_type"),
        }
        transformed_instances.append(transformed_instance)
    return transformed_instances


@timeit
def load_container_instances(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureContainerInstanceSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def cleanup_container_instances(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(
        AzureContainerInstanceSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(
        f"Syncing Azure Container Instances for subscription {subscription_id}."
    )
    raw_groups = get_container_instances(credentials, subscription_id)
    transformed_groups = transform_container_instances(raw_groups)
    load_container_instances(
        neo4j_session, transformed_groups, subscription_id, update_tag
    )
    cleanup_container_instances(neo4j_session, common_job_parameters)
