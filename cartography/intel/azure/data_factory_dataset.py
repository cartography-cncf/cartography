import logging
from typing import Any

import neo4j
from azure.mgmt.datafactory import DataFactoryManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.data_factory.data_factory_dataset import (
    AzureDataFactoryDatasetSchema,
)
from cartography.util import timeit

from .util.common import get_resource_group_from_id
from .util.credentials import Credentials

logger = logging.getLogger(__name__)


@timeit
def get_datasets(
    client: DataFactoryManagementClient,
    rg_name: str,
    factory_name: str,
) -> list[Any]:
    """
    Gets Datasets for a given Data Factory.
    """
    return [d.as_dict() for d in client.datasets.list_by_factory(rg_name, factory_name)]


def transform_datasets(
    datasets_raw: list[Any],
    factory_id: str,
    subscription_id: str,
    linked_service_name_to_id: dict[str, str],
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for d in datasets_raw:
        dataset_id = d.get("id")
        if not dataset_id:
            continue

        ls_name = (
            d.get("properties", {}).get("linked_service_name", {}).get("reference_name")
        )
        linked_service_id = linked_service_name_to_id.get(ls_name)

        transformed.append(
            {
                "id": dataset_id,
                "name": d.get("name"),
                "type": d.get("properties", {}).get("type"),
                "factory_id": factory_id,
                "subscription_id": subscription_id,
                "linked_service_id": linked_service_id,
            },
        )
    return transformed


@timeit
def load_datasets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureDataFactoryDatasetSchema(),
        data,
        lastupdated=update_tag,
        subscription_id=subscription_id,
    )


@timeit
def cleanup_data_factory_datasets(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(
        AzureDataFactoryDatasetSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_data_factory_datasets(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    factories: list[dict[str, Any]],
    linked_services: dict[str, list[dict[str, Any]]],
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> dict[str, list[dict[str, Any]]]:
    client = DataFactoryManagementClient(credentials.credential, subscription_id)
    logger.info("Syncing Azure Data Factory Datasets for subscription.")
    all_transformed_datasets: list[dict[str, Any]] = []
    datasets_by_factory: dict[str, list[dict[str, Any]]] = {}

    for factory in factories:
        factory_id = factory["id"]
        factory_name = factory["name"]
        rg_name = get_resource_group_from_id(factory_id)

        linked_service_name_to_id: dict[str, str] = {
            ls["name"]: ls["id"] for ls in linked_services.get(factory_id, [])
        }

        datasets_raw = get_datasets(client, rg_name, factory_name)
        transformed_datasets = transform_datasets(
            datasets_raw,
            factory_id,
            subscription_id,
            linked_service_name_to_id,
        )
        all_transformed_datasets.extend(transformed_datasets)
        datasets_by_factory[factory_id] = transformed_datasets

    load_datasets(neo4j_session, all_transformed_datasets, subscription_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["subscription_id"] = subscription_id
    cleanup_data_factory_datasets(neo4j_session, cleanup_job_params)

    return datasets_by_factory
