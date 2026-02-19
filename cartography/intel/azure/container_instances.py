import logging
import re
from typing import Any

import neo4j
from azure.core.exceptions import ClientAuthenticationError
from azure.core.exceptions import HttpResponseError
from azure.mgmt.containerinstance import ContainerInstanceManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.azure.util.tag import transform_tags
from cartography.intel.container_arch import ARCH_SOURCE_IMAGE_REF_HINT
from cartography.intel.container_arch import guess_architecture_from_image_ref
from cartography.models.azure.container_instance import AzureContainerInstanceSchema
from cartography.models.azure.tags.container_instance_tag import (
    AzureContainerInstanceTagsSchema,
)
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)
_SHA256_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")


def _resource_group_from_id(resource_id: str | None) -> str | None:
    if not isinstance(resource_id, str):
        return None
    parts = resource_id.split("/")
    try:
        rg_index = parts.index("resourceGroups")
    except ValueError:
        return None
    if rg_index + 1 >= len(parts):
        return None
    return parts[rg_index + 1]


@timeit
def get_container_instances(
    credentials: Credentials, subscription_id: str
) -> list[dict]:
    try:
        client = ContainerInstanceManagementClient(
            credentials.credential, subscription_id
        )
        # NOTE: Azure Container Instances are called "Container Groups" in the SDK.
        # list() can omit container instanceView details; hydrate with get() when possible.
        groups: list[dict[str, Any]] = []
        for container_group in client.container_groups.list():
            list_item = container_group.as_dict()
            name = list_item.get("name")
            resource_group = list_item.get("resource_group") or _resource_group_from_id(
                list_item.get("id")
            )
            if not name or not resource_group:
                groups.append(list_item)
                continue
            try:
                detailed = client.container_groups.get(
                    resource_group_name=resource_group,
                    container_group_name=name,
                ).as_dict()
                groups.append(detailed)
            except HttpResponseError:
                groups.append(list_item)
        return groups
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(
            f"Failed to get Container Instances for subscription {subscription_id}: {str(e)}"
        )
        return []


def transform_container_instances(container_groups: list[dict]) -> list[dict]:
    def get_group_property(
        group: dict[str, Any], snake_key: str, camel_key: str
    ) -> Any:
        if snake_key in group:
            return group.get(snake_key)
        if camel_key in group:
            return group.get(camel_key)
        properties = group.get("properties") or {}
        if snake_key in properties:
            return properties.get(snake_key)
        return properties.get(camel_key)

    def extract_image_refs(group: dict[str, Any]) -> list[str]:
        containers = get_group_property(group, "containers", "containers") or []
        refs: list[str] = []
        for container in containers:
            image_ref = container.get("image")
            if not image_ref and isinstance(container.get("properties"), dict):
                image_ref = container["properties"].get("image")
            if image_ref:
                refs.append(image_ref)
        return refs

    def extract_image_digests(image_refs: list[str]) -> list[str]:
        digests: list[str] = []
        for image_ref in image_refs:
            if "@sha256:" not in image_ref:
                continue
            digest = image_ref.split("@", 1)[1]
            if digest.startswith("sha256:"):
                digests.append(digest)
        return list(dict.fromkeys(digests))

    def extract_image_digests_from_events(group: dict[str, Any]) -> list[str]:
        containers = get_group_property(group, "containers", "containers") or []
        digests: list[str] = []
        for container in containers:
            instance_view = container.get("instance_view") or container.get(
                "instanceView"
            )
            if not isinstance(instance_view, dict):
                continue
            events = instance_view.get("events")
            if not isinstance(events, list):
                continue
            for event in events:
                message = (event or {}).get("message")
                if not isinstance(message, str):
                    continue
                match = _SHA256_PATTERN.search(message)
                if match:
                    digests.append(match.group(0))
        return list(dict.fromkeys(digests))

    transformed_instances: list[dict[str, Any]] = []
    for group in container_groups:
        image_refs = extract_image_refs(group)
        image_digests = list(
            dict.fromkeys(
                extract_image_digests(image_refs)
                + extract_image_digests_from_events(group)
            )
        )
        architecture = None
        architecture_normalized = "unknown"
        architecture_source = None
        # Prefer digest-based exact image resolution; only apply image-ref guessing
        # when no digest is available on the container group payload.
        if not image_digests and image_refs:
            architecture = image_refs[0]
            architecture_normalized = guess_architecture_from_image_ref(architecture)
            if architecture_normalized != "unknown":
                architecture_source = ARCH_SOURCE_IMAGE_REF_HINT

        ip_data = get_group_property(group, "ip_address", "ipAddress")
        transformed_instance = {
            "id": group.get("id"),
            "name": group.get("name"),
            "location": group.get("location"),
            "type": group.get("type"),
            "provisioning_state": get_group_property(
                group, "provisioning_state", "provisioningState"
            ),
            "ip_address": ip_data.get("ip") if isinstance(ip_data, dict) else None,
            "os_type": get_group_property(group, "os_type", "osType"),
            "architecture": architecture,
            "architecture_normalized": architecture_normalized,
            "architecture_source": architecture_source,
            "image_refs": image_refs,
            "image_digests": image_digests,
            "tags": group.get("tags"),
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
def load_container_instance_tags(
    neo4j_session: neo4j.Session,
    subscription_id: str,
    groups: list[dict],
    update_tag: int,
) -> None:
    """
    Loads tags for Container Instances.
    """
    tags = transform_tags(groups, subscription_id)
    load(
        neo4j_session,
        AzureContainerInstanceTagsSchema(),
        tags,
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
def cleanup_container_instance_tags(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(
        AzureContainerInstanceTagsSchema(), common_job_parameters
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
    load_container_instance_tags(
        neo4j_session, subscription_id, transformed_groups, update_tag
    )
    cleanup_container_instances(neo4j_session, common_job_parameters)
    cleanup_container_instance_tags(neo4j_session, common_job_parameters)
