import logging
from typing import Any

import neo4j
from azure.core.exceptions import ClientAuthenticationError
from azure.core.exceptions import HttpResponseError
from azure.mgmt.containerservice import ContainerServiceClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.aks_cluster import AzureKubernetesClusterSchema
from cartography.models.azure.aks_nodepool import AzureKubernetesNodePoolSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


def _get_resource_group_from_id(resource_id: str) -> str:
    """
    Helper function to parse the resource group name from a full resource ID string.
    """
    # CORRECTED: Convert to lowercase to handle case inconsistencies from the API.
    parts = resource_id.lower().split("/")
    try:
        # The resource group name is always the string after 'resourcegroups'
        rg_index = parts.index("resourcegroups")
        return parts[rg_index + 1]
    except (ValueError, IndexError):
        logger.warning(
            f"Could not parse resource group name from resource ID: {resource_id}"
        )
        return ""


@timeit
def get_aks_clusters(
    client: ContainerServiceClient, subscription_id: str
) -> list[dict]:
    try:
        return [cluster.as_dict() for cluster in client.managed_clusters.list()]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(
            f"Failed to get AKS clusters for subscription {subscription_id}: {str(e)}"
        )
        return []


@timeit
def get_agent_pools(
    client: ContainerServiceClient,
    cluster_name: str,
    resource_group_name: str,
) -> list[dict]:
    try:
        return [
            pool.as_dict()
            for pool in client.agent_pools.list(resource_group_name, cluster_name)
        ]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(
            f"Failed to get agent pools for cluster {cluster_name}: {str(e)}"
        )
        return []


@timeit
def transform_aks_clusters(clusters: list[dict]) -> list[dict]:
    transformed_clusters: list[dict[str, Any]] = []
    for cluster in clusters:
        transformed_cluster = {
            "id": cluster.get("id"),
            "name": cluster.get("name"),
            "location": cluster.get("location"),
            "provisioning_state": cluster.get("properties", {}).get(
                "provisioning_state"
            ),
            "kubernetes_version": cluster.get("properties", {}).get(
                "kubernetes_version"
            ),
            "fqdn": cluster.get("properties", {}).get("fqdn"),
        }
        transformed_clusters.append(transformed_cluster)
    return transformed_clusters


@timeit
def transform_agent_pools(agent_pools: list[dict]) -> list[dict]:
    transformed_pools: list[dict[str, Any]] = []
    for pool in agent_pools:
        transformed_pool = {
            "id": pool.get("id"),
            "name": pool.get("name"),
            "provisioning_state": pool.get("properties", {}).get("provisioning_state"),
            "vm_size": pool.get("properties", {}).get("vm_size"),
            "os_type": pool.get("properties", {}).get("os_type"),
            "count": pool.get("properties", {}).get("count"),
        }
        transformed_pools.append(transformed_pool)
    return transformed_pools


@timeit
def load_aks_clusters(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureKubernetesClusterSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_agent_pools(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureKubernetesNodePoolSchema(),
        data,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


@timeit
def cleanup_clusters(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        AzureKubernetesClusterSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(f"Syncing Azure Kubernetes Service for subscription {subscription_id}.")
    client = ContainerServiceClient(credentials.credential, subscription_id)

    clusters = get_aks_clusters(client, subscription_id)
    transformed_clusters = transform_aks_clusters(clusters)
    load_aks_clusters(neo4j_session, transformed_clusters, subscription_id, update_tag)

    for cluster in clusters:
        cluster_id = cluster.get("id")
        if not cluster_id:
            continue

        resource_group_name = _get_resource_group_from_id(cluster_id)
        if resource_group_name:
            agent_pools = get_agent_pools(client, cluster["name"], resource_group_name)
            transformed_pools = transform_agent_pools(agent_pools)
            load_agent_pools(neo4j_session, transformed_pools, cluster_id, update_tag)

            pool_cleanup_params = common_job_parameters.copy()
            pool_cleanup_params["CLUSTER_ID"] = cluster_id
            GraphJob.from_node_schema(
                AzureKubernetesNodePoolSchema(), pool_cleanup_params
            ).run(neo4j_session)

    cleanup_clusters(neo4j_session, common_job_parameters)
