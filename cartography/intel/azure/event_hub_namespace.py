import logging
from typing import Any

import neo4j
from azure.mgmt.eventhub import EventHubManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.event_hub_namespace import AzureEventHubsNamespaceSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


@timeit
def get_event_hub_namespaces(client: EventHubManagementClient) -> list[Any]:
    """
    Get Event Hub Namespaces from Azure.
    """
    return list(client.namespaces.list())


def transform_namespaces(namespaces_raw: list[Any]) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for ns_raw in namespaces_raw:
        ns = ns_raw.as_dict()
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
def cleanup_namespaces(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        AzureEventHubsNamespaceSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync_event_hub_namespaces(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    logger.info(
        "Syncing Azure Event Hub Namespaces for subscription %s.", subscription_id
    )

    client = EventHubManagementClient(credentials.credential, subscription_id)

    namespaces_raw = get_event_hub_namespaces(client)
    if not namespaces_raw:
        logger.info("No Event Hub Namespaces found.")
        return []

    transformed_namespaces = transform_namespaces(namespaces_raw)

    load_namespaces(neo4j_session, transformed_namespaces, subscription_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["AZURE_SUBSCRIPTION_ID"] = subscription_id
    cleanup_namespaces(neo4j_session, cleanup_job_params)

    return namespaces_raw
