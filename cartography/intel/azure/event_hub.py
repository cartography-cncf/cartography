import logging
from typing import Any

import neo4j
from azure.mgmt.eventhub import EventHubManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.event_hub import AzureEventHubSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


def get_resource_group_from_id(resource_id: str) -> str:
    parts = resource_id.lower().split("/")
    rg_index = parts.index("resourcegroups")
    return parts[rg_index + 1]


@timeit
def get_event_hubs(
    client: EventHubManagementClient, resource_group_name: str, namespace_name: str
) -> list[Any]:
    return list(
        client.event_hubs.list_by_namespace(resource_group_name, namespace_name)
    )


def transform_event_hubs(
    event_hubs_raw: list[Any], namespace_id: str
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for eh_raw in event_hubs_raw:
        eh = eh_raw.as_dict()
        transformed.append(
            {
                "id": eh.get("id"),
                "name": eh.get("name"),
                "status": eh.get("properties", {}).get("status"),
                "partition_count": eh.get("properties", {}).get("partition_count"),
                "message_retention_in_days": eh.get("properties", {}).get(
                    "message_retention_in_days"
                ),
                "namespace_id": namespace_id,
            }
        )
    return transformed


@timeit
def load_event_hubs(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    namespace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureEventHubSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
        namespace_id=namespace_id,
    )


@timeit
def cleanup_event_hubs(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(AzureEventHubSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_event_hubs(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    namespaces: list[Any],
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Syncing Azure Event Hubs for subscription %s.", subscription_id)

    client = EventHubManagementClient(credentials.credential, subscription_id)

    for ns_raw in namespaces:
        try:
            ns_id = ns_raw.id
            ns_name = ns_raw.name
        except AttributeError:
            ns_id = ns_raw.get("id")
            ns_name = ns_raw.get("name")

        if not ns_id:
            continue

        rg_name = get_resource_group_from_id(ns_id)

        if rg_name:
            event_hubs_raw = get_event_hubs(client, rg_name, ns_name)
            transformed_hubs = transform_event_hubs(event_hubs_raw, ns_id)

            load_event_hubs(
                neo4j_session, transformed_hubs, subscription_id, ns_id, update_tag
            )

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["AZURE_SUBSCRIPTION_ID"] = subscription_id
    cleanup_event_hubs(neo4j_session, cleanup_job_params)
