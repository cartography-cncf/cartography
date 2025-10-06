import logging
from typing import Any

import neo4j
from azure.core.exceptions import ClientAuthenticationError, HttpResponseError
from azure.mgmt.datafactory import DataFactoryManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.data_factory import AzureDataFactorySchema
from cartography.models.azure.data_factory_dataset import AzureDataFactoryDatasetSchema
from cartography.models.azure.data_factory_linked_service import AzureDataFactoryLinkedServiceSchema
from cartography.models.azure.data_factory_pipeline import AzureDataFactoryPipelineSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


def _get_resource_group_from_id(resource_id: str) -> str:
    parts = resource_id.lower().split('/')
    try:
        rg_index = parts.index('resourcegroups')
        return parts[rg_index + 1]
    except (ValueError, IndexError):
        logger.warning("Could not parse resource group name from a resource ID.")
        return ""


@timeit
def get_factories(client: DataFactoryManagementClient) -> list[dict]:
    try:
        return [f.as_dict() for f in client.factories.list()]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(f"Failed to get Data Factories: {str(e)}")
        return []


@timeit
def get_pipelines(client: DataFactoryManagementClient, rg_name: str, factory_name: str) -> list[dict]:
    try:
        return [p.as_dict() for p in client.pipelines.list_by_factory(rg_name, factory_name)]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(f"Failed to get pipelines for factory {factory_name}: {str(e)}")
        return []


@timeit
def get_datasets(client: DataFactoryManagementClient, rg_name: str, factory_name: str) -> list[dict]:
    try:
        return [d.as_dict() for d in client.datasets.list_by_factory(rg_name, factory_name)]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(f"Failed to get datasets for factory {factory_name}: {str(e)}")
        return []


@timeit
def get_linked_services(client: DataFactoryManagementClient, rg_name: str, factory_name: str) -> list[dict]:
    try:
        return [ls.as_dict() for ls in client.linked_services.list_by_factory(rg_name, factory_name)]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(f"Failed to get linked services for factory {factory_name}: {str(e)}")
        return []


@timeit
def transform_factories(factories: list[dict]) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for f in factories:
        transformed.append({
            'id': f.get('id'),
            'name': f.get('name'),
            'location': f.get('location'),
            'provisioning_state': f.get('properties', {}).get('provisioning_state'),
            'create_time': f.get('properties', {}).get('create_time'),
            'version': f.get('properties', {}).get('version'),
        })
    return transformed


@timeit
def transform_pipelines(pipelines: list[dict], factory_id: str) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for p in pipelines:
        transformed.append({
            'id': p.get('id'),
            'name': p.get('name'),
            'description': p.get('description'),
            'FACTORY_ID': factory_id,
        })
    return transformed


@timeit
def transform_datasets(datasets: list[dict], factory_id: str) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for d in datasets:
        transformed.append({
            'id': d.get('id'),
            'name': d.get('name'),
            'type': d.get('properties', {}).get('type'),
            'FACTORY_ID': factory_id,
        })
    return transformed


@timeit
def transform_linked_services(linked_services: list[dict], factory_id: str) -> list[dict]:
    transformed: list[dict[str, Any]] = []
    for ls in linked_services:
        transformed.append({
            'id': ls.get('id'),
            'name': ls.get('name'),
            'type': ls.get('properties', {}).get('type'),
            'FACTORY_ID': factory_id,
        })
    return transformed


@timeit
def load_factories(
    neo4j_session: neo4j.Session, data: list[dict[str, Any]], subscription_id: str, update_tag: int,
) -> None:
    load(neo4j_session, AzureDataFactorySchema(), data, lastupdated=update_tag, AZURE_SUBSCRIPTION_ID=subscription_id)


@timeit
def load_pipelines(
    neo4j_session: neo4j.Session, data: list[dict[str, Any]], factory_id: str, update_tag: int,
) -> None:
    load(neo4j_session, AzureDataFactoryPipelineSchema(), data, lastupdated=update_tag, FACTORY_ID=factory_id)


@timeit
def load_datasets(
    neo4j_session: neo4j.Session, data: list[dict[str, Any]], factory_id: str, update_tag: int,
) -> None:
    load(neo4j_session, AzureDataFactoryDatasetSchema(), data, lastupdated=update_tag, FACTORY_ID=factory_id)


@timeit
def load_linked_services(
    neo4j_session: neo4j.Session, data: list[dict[str, Any]], factory_id: str, update_tag: int,
) -> None:
    load(neo4j_session, AzureDataFactoryLinkedServiceSchema(), data, lastupdated=update_tag, FACTORY_ID=factory_id)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(f"Syncing Azure Data Factory for subscription {subscription_id}.")
    client = DataFactoryManagementClient(credentials.credential, subscription_id)

    factories = get_factories(client)
    transformed_factories = transform_factories(factories)
    load_factories(neo4j_session, transformed_factories, subscription_id, update_tag)

    for factory in factories:
        factory_id = factory.get('id')
        if not factory_id:
            continue

        rg_name = _get_resource_group_from_id(factory_id)
        if rg_name:
            # Sync Pipelines
            pipelines = get_pipelines(client, rg_name, factory['name'])
            transformed_pipelines = transform_pipelines(pipelines, factory_id)
            load_pipelines(neo4j_session, transformed_pipelines, factory_id, update_tag)
            pipeline_cleanup_params = common_job_parameters.copy()
            pipeline_cleanup_params["FACTORY_ID"] = factory_id
            GraphJob.from_node_schema(AzureDataFactoryPipelineSchema(), pipeline_cleanup_params).run(neo4j_session)

            # Sync Datasets
            datasets = get_datasets(client, rg_name, factory['name'])
            transformed_datasets = transform_datasets(datasets, factory_id)
            load_datasets(neo4j_session, transformed_datasets, factory_id, update_tag)
            dataset_cleanup_params = common_job_parameters.copy()
            dataset_cleanup_params["FACTORY_ID"] = factory_id
            GraphJob.from_node_schema(AzureDataFactoryDatasetSchema(), dataset_cleanup_params).run(neo4j_session)

            # Sync Linked Services
            linked_services = get_linked_services(client, rg_name, factory['name'])
            transformed_linked_services = transform_linked_services(linked_services, factory_id)
            load_linked_services(neo4j_session, transformed_linked_services, factory_id, update_tag)
            ls_cleanup_params = common_job_parameters.copy()
            ls_cleanup_params["FACTORY_ID"] = factory_id
            GraphJob.from_node_schema(AzureDataFactoryLinkedServiceSchema(), ls_cleanup_params).run(neo4j_session)

    GraphJob.from_node_schema(AzureDataFactorySchema(), common_job_parameters).run(neo4j_session)