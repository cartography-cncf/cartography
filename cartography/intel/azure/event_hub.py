import logging
from typing import Any

import neo4j
from azure.core.exceptions import ClientAuthenticationError
from azure.core.exceptions import HttpResponseError
from azure.mgmt.eventhub import EventHubManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.event_hub import AzureEventHubSchema
from cartography.models.azure.event_hub_namespace import AzureEventHubsNamespaceSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


def _get_resource_group_from_id(resource_id: str) -> str:
    parts = resource_id.lower().split("/")
    try:
        rg_index = parts.index("resourcegroups")
        return parts[rg_index + 1]
    except (ValueError, IndexError):
        logger.warning(
            f"Could not parse resource group name from resource ID: {resource_id}"
        )
        return ""


@timeit
def get_event_hub_namespaces(client: EventHubManagementClient) -> list[dict]:
    try:
        return [n.as_dict() for n in client.namespaces.list()]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(f"Failed to get Event Hub Namespaces: {str(e)}")
        return []


@timeit
def get_event_hubs(
    client: EventHubManagementClient, resource_group_name: str, namespace_name: str
) -> list[dict]:
    try:
        return [
            eh.as_dict()
            for eh in client.event_hubs.list_by_namespace(
                resource_group_name, namespace_name
            )
        ]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(
            f"Failed to get Event Hubs for namespace {namespace_name}: {str(e)}"
        )
        return []


def transform_namespaces(namespaces: list[dict]) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for ns in namespaces:
        transformed.append(
            {
                "id": ns.get("id"),
                "name": ns.get("name"),
                "location": ns.get("location"),
                "sku_name": ns.get("sku", {}).get("name"),
                "sku_tier": ns.get("sku", {}).get("tier"),
                "provisioning_state": ns.get("properties", {}).get(
                    "provisioning_state"
                ),
                "is_auto_inflate_enabled": ns.get("properties", {}).get(
                    "is_auto_inflate_enabled"
                ),
                "maximum_throughput_units": ns.get("properties", {}).get(
                    "maximum_throughput_units"
                ),
            }
        )
    return transformed


def transform_event_hubs(event_hubs: list[dict]) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for eh in event_hubs:
        transformed.append(
            {
                "id": eh.get("id"),
                "name": eh.get("name"),
                "status": eh.get("properties", {}).get("status"),
                "partition_count": eh.get("properties", {}).get("partition_count"),
                "message_retention_in_days": eh.get("properties", {}).get(
                    "message_retention_in_days"
                ),
            }
        )
    return transformed


@timeit
def load_namespaces(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureEventHubsNamespaceSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_event_hubs(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    namespace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureEventHubSchema(),
        data,
        lastupdated=update_tag,
        NAMESPACE_ID=namespace_id,
    )


@timeit
def cleanup_namespaces(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(
        AzureEventHubsNamespaceSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(f"Syncing Azure Event Hub for subscription {subscription_id}.")
    client = EventHubManagementClient(credentials.credential, subscription_id)

    namespaces = get_event_hub_namespaces(client)
    transformed_namespaces = transform_namespaces(namespaces)
    load_namespaces(neo4j_session, transformed_namespaces, subscription_id, update_tag)

    for ns in namespaces:
        ns_id = ns.get("id")
        if not ns_id:
            continue

        rg_name = _get_resource_group_from_id(ns_id)
        if rg_name:
            event_hubs = get_event_hubs(client, rg_name, ns["name"])
            transformed_event_hubs = transform_event_hubs(event_hubs)
            load_event_hubs(neo4j_session, transformed_event_hubs, ns_id, update_tag)

            eh_cleanup_params = common_job_parameters.copy()
            eh_cleanup_params["NAMESPACE_ID"] = ns_id
            GraphJob.from_node_schema(AzureEventHubSchema(), eh_cleanup_params).run(
                neo4j_session
            )

    cleanup_namespaces(neo4j_session, common_job_parameters)
