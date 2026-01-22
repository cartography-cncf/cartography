import logging
from typing import Any

import neo4j
from azure.mgmt.datafactory import DataFactoryManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.data_factory.data_factory_linked_service import (
    AzureDataFactoryLinkedServiceSchema,
)
from cartography.util import timeit

from .util.common import get_resource_group_from_id
from .util.credentials import Credentials

logger = logging.getLogger(__name__)


@timeit
def get_linked_services(
    client: DataFactoryManagementClient,
    rg_name: str,
    factory_name: str,
) -> list[Any]:
    """
    Gets Linked Services for a given Data Factory.
    """
    return [
        ls.as_dict()
        for ls in client.linked_services.list_by_factory(rg_name, factory_name)
    ]


def transform_linked_services(
    linked_services_raw: list[Any],
    factory_id: str,
    subscription_id: str,
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for ls in linked_services_raw:
        transformed.append(
            {
                "id": ls.get("id"),
                "name": ls.get("name"),
                "type": ls.get("properties", {}).get("type"),
                "factory_id": factory_id,
                "subscription_id": subscription_id,
            },
        )
    return transformed


@timeit
def load_linked_services(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureDataFactoryLinkedServiceSchema(),
        data,
        lastupdated=update_tag,
        subscription_id=subscription_id,
    )


@timeit
def cleanup_data_factory_linked_services(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(
        AzureDataFactoryLinkedServiceSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_data_factory_linked_services(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    factories: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> dict[str, list[dict[str, Any]]]:
    client = DataFactoryManagementClient(credentials.credential, subscription_id)
    logger.info("Syncing Azure Data Factory Linked Services for subscription.")
    all_transformed_linked_services: list[dict[str, Any]] = []
    linked_services_by_factory: dict[str, list[dict[str, Any]]] = {}

    for factory in factories:
        factory_id = factory["id"]
        factory_name = factory["name"]
        rg_name = get_resource_group_from_id(factory_id)

        linked_services_raw = get_linked_services(client, rg_name, factory_name)
        transformed_linked_services = transform_linked_services(
            linked_services_raw,
            factory_id,
            subscription_id,
        )
        all_transformed_linked_services.extend(transformed_linked_services)
        linked_services_by_factory[factory_id] = transformed_linked_services

    load_linked_services(
        neo4j_session,
        all_transformed_linked_services,
        subscription_id,
        update_tag,
    )

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["subscription_id"] = subscription_id
    cleanup_data_factory_linked_services(neo4j_session, cleanup_job_params)

    return linked_services_by_factory
