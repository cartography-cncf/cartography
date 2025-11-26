import logging
from typing import Any

import neo4j
from azure.mgmt.datafactory import DataFactoryManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.data_factory.data_factory_pipeline import (
    AzureDataFactoryPipelineSchema,
)
from cartography.util import timeit

from .util.common import get_resource_group_from_id
from .util.credentials import Credentials

logger = logging.getLogger(__name__)


@timeit
def get_pipelines(
    client: DataFactoryManagementClient,
    rg_name: str,
    factory_name: str,
) -> list[Any]:
    """
    Gets Pipelines for a given Data Factory.
    """
    return [
        p.as_dict() for p in client.pipelines.list_by_factory(rg_name, factory_name)
    ]


def transform_pipelines(
    pipelines_raw: list[Any],
    factory_id: str,
    subscription_id: str,
    dataset_name_to_id: dict[str, str],
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for p in pipelines_raw:
        pipeline_id = p.get("id")
        if not pipeline_id:
            continue

        dataset_references: list[str] = []
        activities = p.get("activities", [])

        for activity in activities:
            for input_ref in activity.get("inputs", []):
                ref_name = input_ref.get("reference_name")
                if ref_name and ref_name in dataset_name_to_id:
                    dataset_references.append(dataset_name_to_id[ref_name])
            for output_ref in activity.get("outputs", []):
                ref_name = output_ref.get("reference_name")
                if ref_name and ref_name in dataset_name_to_id:
                    dataset_references.append(dataset_name_to_id[ref_name])

        # Create a new dict for each relationship
        for dataset_id in set(dataset_references):
            transformed.append(
                {
                    "id": pipeline_id,
                    "name": p.get("name"),
                    "description": p.get("properties", {}).get("description"),
                    "factory_id": factory_id,
                    "subscription_id": subscription_id,
                    "dataset_id": dataset_id,
                },
            )

    return transformed


@timeit
def load_pipelines(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureDataFactoryPipelineSchema(),
        data,
        lastupdated=update_tag,
        subscription_id=subscription_id,
    )


@timeit
def cleanup_data_factory_pipelines(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(
        AzureDataFactoryPipelineSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_data_factory_pipelines(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    factories: list[dict[str, Any]],
    datasets: dict[str, list[dict[str, Any]]],
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    client = DataFactoryManagementClient(credentials.credential, subscription_id)
    logger.info("Syncing Azure Data Factory Pipelines for subscription.")
    all_transformed_pipelines: list[dict[str, Any]] = []

    for factory in factories:
        factory_id = factory["id"]
        factory_name = factory["name"]
        rg_name = get_resource_group_from_id(factory_id)

        dataset_name_to_id: dict[str, str] = {
            ds["name"]: ds["id"] for ds in datasets.get(factory_id, [])
        }

        pipelines_raw = get_pipelines(client, rg_name, factory_name)
        transformed_pipelines = transform_pipelines(
            pipelines_raw,
            factory_id,
            subscription_id,
            dataset_name_to_id,
        )
        all_transformed_pipelines.extend(transformed_pipelines)

    load_pipelines(
        neo4j_session,
        all_transformed_pipelines,
        subscription_id,
        update_tag,
    )

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["subscription_id"] = subscription_id
    cleanup_data_factory_pipelines(neo4j_session, cleanup_job_params)
