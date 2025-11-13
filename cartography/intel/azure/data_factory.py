import logging
from typing import Any

import neo4j
from azure.mgmt.datafactory import DataFactoryManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.data_factory.data_factory import AzureDataFactorySchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


@timeit
def get_factories(client: DataFactoryManagementClient) -> list[Any]:
    """
    Gets Data Factories for the subscription.
    """
    return [f.as_dict() for f in client.factories.list()]


def transform_factories(factories_raw: list[Any]) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for f in factories_raw:
        transformed.append(
            {
                "id": f.get("id"),
                "name": f.get("name"),
                "location": f.get("location"),
                "provisioning_state": f.get("properties", {}).get("provisioning_state"),
                "create_time": f.get("properties", {}).get("create_time"),
                "version": f.get("properties", {}).get("version"),
            },
        )
    return transformed


@timeit
def load_factories(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureDataFactorySchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def cleanup_data_factories(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(AzureDataFactorySchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_data_factories(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> list[dict[str, Any]]:
    client = DataFactoryManagementClient(credentials.credential, subscription_id)
    logger.info("Syncing Azure Data Factories for subscription.")
    factories_raw_as_dict = get_factories(client)

    transformed_factories = transform_factories(factories_raw_as_dict)
    load_factories(neo4j_session, transformed_factories, subscription_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["subscription_id"] = subscription_id
    cleanup_data_factories(neo4j_session, cleanup_job_params)

    return factories_raw_as_dict
