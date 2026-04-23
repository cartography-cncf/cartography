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
        return [cg.as_dict() for cg in client.container_groups.list()]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(
            f"Failed to get Container Instances for subscription {subscription_id}: {str(e)}"
        )
        return []


def transform_container_instances(container_groups: list[dict]) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for group in container_groups:
        group_id = group.get("id")
        for container in group.get("containers", []):
            image = container.get("image")
            try:
                image_digest = image.split("@")[1] if image else None
            except IndexError:
                image_digest = None

            resources = container.get("resources", {})
            requests = resources.get("requests", {})
            limits = resources.get("limits", {})

            # Per-container runtime state lives on instance_view.current_state.state,
            # separate from the container group's provisioning_state.
            instance_view = container.get("instance_view") or {}
            current_state = instance_view.get("current_state") or {}
            state = current_state.get("state")

            transformed.append(
                {
                    "id": f"{group_id}/{container.get('name')}",
                    "name": container.get("name"),
                    "group_id": group_id,
                    "image": image,
                    "image_digest": image_digest,
                    # ACI does not expose host architecture via its API, and ARM64 support
                    # is not yet GA. All ACI workloads run on amd64 hosts.
                    "architecture": "amd64",
                    "architecture_normalized": "amd64",
                    "state": state,
                    "cpu_request": requests.get("cpu"),
                    "memory_request_gb": requests.get("memory_in_gb"),
                    "cpu_limit": limits.get("cpu"),
                    "memory_limit_gb": limits.get("memory_in_gb"),
                },
            )
    return transformed


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
    transformed = transform_container_instances(raw_groups)
    load_container_instances(neo4j_session, transformed, subscription_id, update_tag)
    cleanup_container_instances(neo4j_session, common_job_parameters)
