import logging
from typing import Any

import neo4j
from azure.core.exceptions import ClientAuthenticationError
from azure.core.exceptions import HttpResponseError
from azure.mgmt.synapse import SynapseManagementClient
from azure.synapse.artifacts import ArtifactsClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.synapse.dedicated_sql_pool import (
    AzureSynapseDedicatedSqlPoolSchema,
)
from cartography.models.azure.synapse.linked_service import (
    AzureSynapseLinkedServiceSchema,
)
from cartography.models.azure.synapse.managed_private_endpoint import (
    AzureSynapseManagedPrivateEndpointSchema,
)
from cartography.models.azure.synapse.pipeline import AzureSynapsePipelineSchema
from cartography.models.azure.synapse.spark_pool import AzureSynapseSparkPoolSchema
from cartography.models.azure.synapse.workspace import AzureSynapseWorkspaceSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


def _get_resource_group_from_id(resource_id: str) -> str:
    """
    Helper function to parse the resource group name from a full resource ID string.
    """
    parts = resource_id.lower().split("/")
    rg_index = parts.index("resourcegroups")
    return parts[rg_index + 1]


@timeit
def get_synapse_workspaces(client: SynapseManagementClient) -> list[dict]:
    """Gets Synapse Workspaces using the management client"""
    try:
        return [w.as_dict() for w in client.workspaces.list()]
    except ClientAuthenticationError:
        logger.warning(
            "Failed to get Synapse workspaces due to a client authentication error.",
            exc_info=True,
        )
        raise
    except HttpResponseError:
        logger.warning(
            "Failed to get Synapse workspaces due to an HTTP error.", exc_info=True
        )
        raise


@timeit
def get_dedicated_sql_pools(
    client: SynapseManagementClient, rg_name: str, workspace_name: str
) -> list[dict]:
    """Gets Dedicated SQL Pools using the management client"""
    try:
        return [
            p.as_dict()
            for p in client.sql_pools.list_by_workspace(rg_name, workspace_name)
        ]
    except HttpResponseError:
        logger.warning(
            f"Failed to get dedicated SQL pools for workspace {workspace_name}.",
            exc_info=True,
        )
        return []


@timeit
def get_spark_pools(
    client: SynapseManagementClient, rg_name: str, workspace_name: str
) -> list[dict]:
    """Gets Spark Pools using the management client"""
    try:
        return [
            p.as_dict()
            for p in client.big_data_pools.list_by_workspace(rg_name, workspace_name)
        ]
    except HttpResponseError:
        logger.warning(
            f"Failed to get Spark pools for workspace {workspace_name}.", exc_info=True
        )
        return []


@timeit
def get_pipelines(credential: Any, endpoint: str) -> list[dict]:
    """Gets pipelines using artifacts client"""
    try:
        client = ArtifactsClient(endpoint=endpoint, credential=credential)
        return [p.as_dict() for p in client.pipeline.get_pipelines_by_workspace()]
    except HttpResponseError:
        logger.warning(
            f"Failed to get pipelines for workspace endpoint {endpoint}.", exc_info=True
        )
        return []


@timeit
def get_linked_services(credential: Any, endpoint: str) -> list[dict]:
    """Gets linked services using artifacts client"""
    try:
        client = ArtifactsClient(endpoint=endpoint, credential=credential)
        return [
            ls.as_dict()
            for ls in client.linked_service.get_linked_services_by_workspace()
        ]
    except HttpResponseError:
        logger.warning(
            f"Failed to get linked services for workspace endpoint {endpoint}.",
            exc_info=True,
        )
        return []


@timeit
def get_managed_private_endpoints(
    client: SynapseManagementClient, rg_name: str, workspace_name: str
) -> list[dict]:
    """Gets Managed Private Endpoints using the management client"""
    try:
        return [
            pe.as_dict()
            for pe in client.managed_private_endpoints.list(
                rg_name, workspace_name, "default"
            )
        ]
    except AttributeError:
        logger.warning(
            "The installed azure-mgmt-synapse SDK version does not have the expected "
            "'managed_private_endpoints.list' method. Skipping MPEs."
        )
        return []
    except HttpResponseError:
        logger.warning(
            f"Failed to get managed private endpoints for workspace {workspace_name}.",
            exc_info=True,
        )
        return []


# --- Transform Functions ---


def transform_workspaces(workspaces: list[dict]) -> list[dict]:
    transformed = []
    for ws in workspaces:
        transformed.append(
            {
                "id": ws["id"],
                "name": ws.get("name"),
                "location": ws.get("location"),
                "connectivity_endpoints": str(ws.get("connectivity_endpoints")),
            }
        )
    return transformed


def transform_dedicated_sql_pools(sql_pools: list[dict]) -> list[dict]:
    transformed = []
    for pool in sql_pools:
        transformed.append(
            {
                "id": pool["id"],
                "name": pool.get("name"),
                "location": pool.get("location"),
                "provisioning_state": pool.get("properties", {}).get(
                    "provisioningState"
                ),
                "sku": pool.get("sku", {}).get("name"),
            }
        )
    return transformed


def transform_spark_pools(spark_pools: list[dict]) -> list[dict]:
    transformed = []
    for pool in spark_pools:
        properties = pool.get("properties", {})
        transformed.append(
            {
                "id": pool["id"],
                "name": pool.get("name"),
                "location": pool.get("location"),
                "provisioning_state": properties.get("provisioning_state"),
                "node_size": properties.get("node_size"),
                "node_count": properties.get("node_count"),
                "spark_version": properties.get("spark_version"),
            }
        )
    return transformed


def transform_pipelines(pipelines: list[dict]) -> list[dict]:
    transformed = []
    for p in pipelines:
        transformed.append({"id": p["id"], "name": p.get("name")})
    return transformed


def transform_linked_services(linked_services: list[dict]) -> list[dict]:
    transformed = []
    for ls in linked_services:
        transformed.append(
            {
                "id": ls["id"],
                "name": ls.get("name"),
            }
        )
    return transformed


def transform_managed_private_endpoints(endpoints: list[dict]) -> list[dict]:
    transformed = []
    for pe in endpoints:
        transformed.append(
            {
                "id": pe["id"],
                "name": pe.get("name"),
                "target_resource_id": pe.get("properties", {}).get(
                    "privateLinkResourceId"
                ),
            }
        )
    return transformed


# --- Load Functions ---


@timeit
def load_synapse_workspaces(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    """Loads AzureSynapseWorkspace nodes"""
    load(
        neo4j_session,
        AzureSynapseWorkspaceSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_dedicated_sql_pools(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    subscription_id: str,
    update_tag: int,
) -> None:
    """Loads AzureSynapseDedicatedSqlPool nodes"""
    load(
        neo4j_session,
        AzureSynapseDedicatedSqlPoolSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_spark_pools(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    subscription_id: str,
    update_tag: int,
) -> None:
    """Loads AzureSynapseSparkPool nodes"""
    load(
        neo4j_session,
        AzureSynapseSparkPoolSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_pipelines(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    subscription_id: str,
    update_tag: int,
) -> None:
    """Loads AzureSynapsePipeline nodes"""
    load(
        neo4j_session,
        AzureSynapsePipelineSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_linked_services(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    subscription_id: str,
    update_tag: int,
) -> None:
    """Loads AzureSynapseLinkedService nodes"""
    load(
        neo4j_session,
        AzureSynapseLinkedServiceSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_managed_private_endpoints(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    subscription_id: str,
    update_tag: int,
) -> None:
    """Loads AzureSynapseManagedPrivateEndpoint nodes"""
    load(
        neo4j_session,
        AzureSynapseManagedPrivateEndpointSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def _sync_workspaces(
    neo4j_session: neo4j.Session,
    mgmt_client: SynapseManagementClient,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> list[dict]:
    """Syncs Synapse Workspaces and returns the raw data for child processing"""
    workspaces_raw = get_synapse_workspaces(mgmt_client)
    if not workspaces_raw:
        return []

    workspaces = transform_workspaces(workspaces_raw)
    load_synapse_workspaces(neo4j_session, workspaces, subscription_id, update_tag)
    return workspaces_raw


@timeit
def _sync_sql_pools(
    neo4j_session: neo4j.Session,
    mgmt_client: SynapseManagementClient,
    workspace_raw_data: dict,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    """Syncs Dedicated SQL Pools for a given workspace"""
    ws_id = workspace_raw_data["id"]
    rg_name = _get_resource_group_from_id(ws_id)
    ws_name = workspace_raw_data["name"]

    sql_pools = get_dedicated_sql_pools(mgmt_client, rg_name, ws_name)
    if sql_pools:
        transformed_sql_pools = transform_dedicated_sql_pools(sql_pools)
        valid_sql_pools = [p for p in transformed_sql_pools if p.get("id")]
        if valid_sql_pools:
            load_dedicated_sql_pools(
                neo4j_session, valid_sql_pools, ws_id, subscription_id, update_tag
            )


@timeit
def _sync_spark_pools(
    neo4j_session: neo4j.Session,
    mgmt_client: SynapseManagementClient,
    workspace_raw_data: dict,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    """Syncs Spark Pools for a given workspace"""
    ws_id = workspace_raw_data["id"]
    rg_name = _get_resource_group_from_id(ws_id)
    ws_name = workspace_raw_data["name"]

    spark_pools = get_spark_pools(mgmt_client, rg_name, ws_name)
    if spark_pools:
        transformed_spark_pools = transform_spark_pools(spark_pools)
        valid_spark_pools = [p for p in transformed_spark_pools if p.get("id")]
        if valid_spark_pools:
            load_spark_pools(
                neo4j_session, valid_spark_pools, ws_id, subscription_id, update_tag
            )


@timeit
def _sync_artifacts(
    neo4j_session: neo4j.Session,
    credential: Any,
    workspace_raw_data: dict,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    """Syncs Pipelines and Linked Services using the artifacts client"""
    ws_id = workspace_raw_data["id"]
    ws_name = workspace_raw_data["name"]
    workspace_dev_endpoint = workspace_raw_data.get("connectivity_endpoints", {}).get(
        "dev"
    )

    if not workspace_dev_endpoint:
        logger.warning(
            f"Could not find development endpoint for Synapse workspace {ws_name}. Skipping artifacts sync."
        )
        return

    # Sync Pipelines
    pipelines_raw = get_pipelines(credential, workspace_dev_endpoint)
    if pipelines_raw:
        pipelines = transform_pipelines(pipelines_raw)
        valid_pipelines = [p for p in pipelines if p.get("id")]
        if valid_pipelines:
            load_pipelines(
                neo4j_session, valid_pipelines, ws_id, subscription_id, update_tag
            )

    # Sync Linked Services
    linked_services_raw = get_linked_services(credential, workspace_dev_endpoint)
    if linked_services_raw:
        linked_services = transform_linked_services(linked_services_raw)
        valid_linked_services = [ls for ls in linked_services if ls.get("id")]
        if valid_linked_services:
            load_linked_services(
                neo4j_session, valid_linked_services, ws_id, subscription_id, update_tag
            )
        # TODO: Add logic to create CONNECTS_TO relationships for linked services.


def _sync_managed_private_endpoints(
    neo4j_session: neo4j.Session,
    mgmt_client: SynapseManagementClient,
    workspace_raw_data: dict,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    """Syncs Managed Private Endpoints for a given workspace"""
    ws_id = workspace_raw_data["id"]
    rg_name = _get_resource_group_from_id(ws_id)
    ws_name = workspace_raw_data["name"]

    private_endpoints_raw = get_managed_private_endpoints(mgmt_client, rg_name, ws_name)
    if private_endpoints_raw:
        private_endpoints = transform_managed_private_endpoints(private_endpoints_raw)
        valid_private_endpoints = [pe for pe in private_endpoints if pe.get("id")]
        if valid_private_endpoints:
            load_managed_private_endpoints(
                neo4j_session,
                valid_private_endpoints,
                ws_id,
                subscription_id,
                update_tag,
            )
        # TODO: Add logic to create CONNECTS_TO relationships for private endpoints.


# --- Main Sync Function ---


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(f"Syncing Azure Synapse for subscription {subscription_id}.")
    mgmt_client = SynapseManagementClient(credentials.credential, subscription_id)

    workspaces_raw = _sync_workspaces(
        neo4j_session, mgmt_client, subscription_id, update_tag, common_job_parameters
    )

    if workspaces_raw:
        for ws_raw in workspaces_raw:
            _sync_sql_pools(
                neo4j_session,
                mgmt_client,
                ws_raw,
                subscription_id,
                update_tag,
                common_job_parameters,
            )
            _sync_spark_pools(
                neo4j_session,
                mgmt_client,
                ws_raw,
                subscription_id,
                update_tag,
                common_job_parameters,
            )
            _sync_managed_private_endpoints(
                neo4j_session,
                mgmt_client,
                ws_raw,
                subscription_id,
                update_tag,
                common_job_parameters,
            )
            _sync_artifacts(
                neo4j_session,
                credentials.credential,
                ws_raw,
                subscription_id,
                update_tag,
                common_job_parameters,
            )

    GraphJob.from_node_schema(AzureSynapseWorkspaceSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(
        AzureSynapseDedicatedSqlPoolSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(AzureSynapseSparkPoolSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(AzureSynapsePipelineSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(
        AzureSynapseLinkedServiceSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        AzureSynapseManagedPrivateEndpointSchema(), common_job_parameters
    ).run(neo4j_session)
