import logging
from typing import Dict
from typing import List

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from azure.mgmt.containerservice import ContainerServiceClient
from cloudconsolelink.clouds.azure import AzureLinker

from .util.credentials import Credentials
from cartography.util import get_azure_resource_group_name
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
azure_console_link = AzureLinker()


def load_aks_managed_clusters(
    session: neo4j.Session, subscription_id: str, data_list: List[Dict], update_tag: int,
) -> None:
    session.execute_write(_load_aks_managed_clusters_tx, subscription_id, data_list, update_tag)


def load_aks_managed_cluster_agentpools(
    session: neo4j.Session, cluster_id: str, data_list: List[Dict], update_tag: int,
) -> None:
    session.execute_write(_load_aks_managed_cluster_agentpools_tx, cluster_id, data_list, update_tag)


def load_container_registries(
    session: neo4j.Session,
    subscription_id: str,
    data_list: List[Dict],
    update_tag: int,
) -> None:
    session.execute_write(_load_container_registries_tx, subscription_id, data_list, update_tag)


def load_container_registry_replications(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_container_registry_replications_tx, data_list, update_tag)


def load_container_registry_runs(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_container_registry_runs_tx, data_list, update_tag)


def load_container_registry_tasks(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_container_registry_tasks_tx, data_list, update_tag)


def load_container_registry_webhooks(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_container_registry_webhooks_tx, data_list, update_tag)


def load_container_groups(session: neo4j.Session, subscription_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_container_groups_tx, subscription_id, data_list, update_tag)


def load_containers(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_containers_tx, data_list, update_tag)


@timeit
def get_client(credentials: Credentials, subscription_id: str) -> ContainerServiceClient:
    client = ContainerServiceClient(credentials, subscription_id)
    return client


@timeit
def get_container_registry_Client(credentials: Credentials, subscription_id: str) -> ContainerRegistryManagementClient:
    client = ContainerRegistryManagementClient(credentials, subscription_id)
    return client


@timeit
def get_container_instance_Client(credentials: Credentials, subscription_id: str) -> ContainerInstanceManagementClient:
    client = ContainerInstanceManagementClient(credentials, subscription_id)
    return client


@timeit
def get_aks_managed_clusters_list(
    credentials: Credentials, subscription_id: str, regions: list, common_job_parameters: Dict,
) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        aks_managed_clusters_list = list(map(lambda x: x.as_dict(), client.managed_clusters.list()))
        aks_managed_clusters_data = []
        for aks in aks_managed_clusters_list:
            aks["resource_group"] = get_azure_resource_group_name(aks.get("id"))
            aks["publicNetworkAccess"] = aks.get("properties", {}).get("public_network_access", "Disabled")
            aks["consolelink"] = azure_console_link.get_console_link(
                id=aks["id"],
                primary_ad_domain_name=common_job_parameters["Azure_Primary_AD_Domain_Name"],
            )
            if regions is None:
                aks_managed_clusters_data.append(aks)
            else:
                if aks.get("location") in regions or aks.get("location") == "global":
                    aks_managed_clusters_data.append(aks)
        return aks_managed_clusters_data

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving AKS - {e}")
        return []


def _load_aks_managed_clusters_tx(
    tx: neo4j.Transaction, subscription_id: str, aks_managed_clusters_list: List[Dict], update_tag: int,
) -> None:
    ingest_aks_managed_clusters = """
    UNWIND $aks_managed_clusters_list AS aks
    MERGE (a:AzureCluster{id: aks.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = aks.type,
    a.location = aks.location,
    a.region = aks.location,
    a.publicNetworkAccess = aks.publicNetworkAccess,
    a.consolelink = aks.consolelink,
    a.resourcegroup = aks.resource_group
    SET a.lastupdated = $update_tag,
    a.name = aks.name
    WITH a
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_aks_managed_clusters,
        aks_managed_clusters_list=aks_managed_clusters_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )
    for aks in aks_managed_clusters_list:
        resource_group = get_azure_resource_group_name(aks.get("id"))
        _attach_resource_group_aks(tx, aks["id"], resource_group, update_tag)


def _attach_resource_group_aks(tx: neo4j.Transaction, aks_id: str, resource_group: str, update_tag: int) -> None:
    ingest_aks_resource = """
    MATCH (a:AzureCluster{id: $aks_id})
    WITH a
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (a)-[res:RESOURCE_GROUP]->(rg)
    ON CREATE SET res.firstseen = timestamp()
    SET res.lastupdated = $update_tag
    """
    tx.run(
        ingest_aks_resource,
        aks_id=aks_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


@timeit
def get_aks_managed_cluster_agentpools_list(
    credentials: Credentials,
    subscription_id: str,
    resource_group_name: str,
    cluster_name: str,
    common_job_parameters: Dict,
) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        agentpools_list = list(
            map(
                lambda x: x.as_dict(),
                client.agent_pools.list(resource_group_name=resource_group_name, resource_name=cluster_name),
            ),
        )
        agentpools_data = []
        for agentpool in agentpools_list:
            agentpool["resource_group"] = get_azure_resource_group_name(agentpool.get("id"))
            agentpool["consolelink"] = azure_console_link.get_console_link(
                id=agentpool["id"],
                primary_ad_domain_name=common_job_parameters["Azure_Primary_AD_Domain_Name"],
            )
            agentpools_data.append(agentpool)
        return agentpools_data

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving AKS agent pools - {e}")
        return []


def _load_aks_managed_cluster_agentpools_tx(
    tx: neo4j.Transaction, cluster_id: str, agentpools_list: List[Dict], update_tag: int,
) -> None:
    ingest_aks_agentpools = """
    UNWIND $agentpools_list AS pool
    MERGE (a:AzureClusterAgentPool{id: pool.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = pool.type,
    a.count = pool.count,
    a.host_group_id = pool.host_group_id,
    a.max_pods = pool.max_pods,
    a.consolelink = pool.consolelink,
    a.resourcegroup = pool.resource_group
    SET a.lastupdated = $update_tag,
    a.name = pool.name
    WITH a
    MATCH (c:AzureCluster{id: $cluster_id})
    MERGE (c)-[r:HAS]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_aks_agentpools,
        agentpools_list=agentpools_list,
        cluster_id=cluster_id,
        update_tag=update_tag,
    )


def cleanup_aks(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("azure_import_aks_cleanup.json", neo4j_session, common_job_parameters)


def sync_aks(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: Dict,
    regions: list,
) -> None:
    aks_managed_clusters_list = get_aks_managed_clusters_list(
        credentials, subscription_id, regions, common_job_parameters,
    )

    load_aks_managed_clusters(neo4j_session, subscription_id, aks_managed_clusters_list, update_tag)
    for cluster in aks_managed_clusters_list:
        agent_pools = get_aks_managed_cluster_agentpools_list(
            credentials, subscription_id, cluster["resource_group"], cluster["name"], common_job_parameters,
        )
        load_aks_managed_cluster_agentpools(neo4j_session, cluster["id"], agent_pools, update_tag)
    cleanup_aks(neo4j_session, common_job_parameters)


@timeit
def get_container_registries_list(
    client: ContainerRegistryManagementClient, regions: list, common_job_parameters: Dict,
) -> List[Dict]:
    try:
        container_registries_list = list(map(lambda x: x.as_dict(), client.registries.list()))
        registry_data = []
        for registry in container_registries_list:
            registry["resource_group"] = get_azure_resource_group_name(registry.get("id"))
            registry["consolelink"] = azure_console_link.get_console_link(
                id=registry["id"],
                primary_ad_domain_name=common_job_parameters["Azure_Primary_AD_Domain_Name"],
            )
            if regions is None:
                registry_data.append(registry)
            else:
                if registry.get("location") in regions or registry.get("location") == "global":
                    registry_data.append(registry)

        return registry_data

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving registries - {e}")
        return []


def _load_container_registries_tx(
    tx: neo4j.Transaction,
    subscription_id: str,
    container_registries_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_container_registry = """
    UNWIND $container_registries_list AS registry
    MERGE (a:AzureContainerRegistry{id: registry.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = registry.type,
    a.location = registry.location,
    a.region = registry.location,
    a.consolelink = registry.consolelink,
    a.resourcegroup = registry.resource_group
    SET a.lastupdated = $update_tag,
    a.name = registry.name
    WITH a
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_container_registry,
        container_registries_list=container_registries_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )
    for container_registries in container_registries_list:
        resource_group = get_azure_resource_group_name(container_registries.get("id"))
        _attach_resource_group_container_registry(tx, container_registries["id"], resource_group, update_tag)


def _attach_resource_group_container_registry(
    tx: neo4j.Transaction, container_registry_id: List[Dict], resource_group: str, update_tag: int,
) -> None:
    ingest_container_registry = """
    MATCH (a:AzureContainerRegistry{id: $container_registry_id})
    WITH a
    MATCH (rg:AzureResourceGroup{name:$resource_group })
    MERGE (a)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_container_registry,
        container_registry_id=container_registry_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


def cleanup_container_registries(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("azure_import_container_registries_cleanup.json", neo4j_session, common_job_parameters)


def sync_container_registries(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: Dict,
    regions: list,
) -> None:
    client = get_container_registry_Client(credentials, subscription_id)
    container_registries_list = get_container_registries_list(client, regions, common_job_parameters)

    load_container_registries(neo4j_session, subscription_id, container_registries_list, update_tag)
    cleanup_container_registries(neo4j_session, common_job_parameters)
    sync_container_registry_replications(
        neo4j_session,
        client,
        container_registries_list,
        update_tag,
        common_job_parameters,
    )
    sync_container_registry_runs(
        neo4j_session,
        client,
        container_registries_list,
        update_tag,
        common_job_parameters,
    )
    sync_container_registry_tasks(
        neo4j_session,
        client,
        container_registries_list,
        update_tag,
        common_job_parameters,
    )
    sync_container_registry_webhooks(
        neo4j_session,
        client,
        container_registries_list,
        update_tag,
        common_job_parameters,
    )


@timeit
def get_container_registry_replications_list(
    client: ContainerRegistryManagementClient,
    container_registries_list: List[Dict],
    common_job_parameters: Dict,
) -> List[Dict]:
    try:
        container_registry_replications_list: List[Dict] = []
        for container_registry in container_registries_list:
            container_registry_replications_list = container_registry_replications_list + list(
                map(
                    lambda x: x.as_dict(),
                    client.replications.list(
                        registry_name=container_registry["name"],
                        resource_group_name=container_registry["resource_group"],
                    ),
                ),
            )

        for replication in container_registry_replications_list:
            replication["resource_group"] = get_azure_resource_group_name(replication.get("id"))
            replication["container_registry_id"] = replication["id"][: replication["id"].index("/replications")]
            replication["consolelink"] = azure_console_link.get_console_link(
                id=replication["id"],
                primary_ad_domain_name=common_job_parameters["Azure_Primary_AD_Domain_Name"],
            )

        return container_registry_replications_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving container_registry_replications - {e}")
        return []


def _load_container_registry_replications_tx(
    tx: neo4j.Transaction,
    container_registry_replications_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_container_replication = """
    UNWIND $container_registry_replications_list AS replication
    MERGE (a:AzureContainerRegistryReplication{id: replication.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = replication.type,
    a.location = replication.location,
    a.region = replication.location,
    a.consolelink = replication.consolelink,
    a.resourcegroup = replication.resource_group
    SET a.lastupdated = $update_tag,
    a.name = replication.name
    WITH a,replication
    MATCH (owner:AzureContainerRegistry{id: replication.container_registry_id})
    MERGE (owner)-[r:CONTAIN]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_container_replication,
        container_registry_replications_list=container_registry_replications_list,
        update_tag=update_tag,
    )
    for container_registry_replication in container_registry_replications_list:
        resource_group = get_azure_resource_group_name(container_registry_replication.get("id"))
        _attach_resource_group_container_replication(
            tx, container_registry_replication["id"], resource_group, update_tag=update_tag,
        )


def _attach_resource_group_container_replication(
    tx: neo4j.Transaction, container_registry_replication_id: str, resource_group: str, update_tag: int,
) -> None:
    ingest_container_replication = """
        MATCH (a:AzureContainerRegistryReplication{id: $container_registry_replication_id})
        WITH a
        MATCH (rg:AzureResourceGroup{name:$resource_group})
        MERGE (a)-[r:RESOURCE_GROUP]->(rg)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_container_replication,
        container_registry_replication_id=container_registry_replication_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


def cleanup_container_registry_replications(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("azure_import_container_registry_replications_cleanup.json", neo4j_session, common_job_parameters)


def sync_container_registry_replications(
    neo4j_session: neo4j.Session,
    client: ContainerRegistryManagementClient,
    container_registries_list: List[Dict],
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    container_registry_replications_list = get_container_registry_replications_list(
        client,
        container_registries_list,
        common_job_parameters,
    )
    load_container_registry_replications(neo4j_session, container_registry_replications_list, update_tag)
    cleanup_container_registry_replications(neo4j_session, common_job_parameters)


@timeit
def get_container_registry_runs_list(
    client: ContainerRegistryManagementClient,
    container_registries_list: List[Dict],
    common_job_parameters: Dict,
) -> List[Dict]:
    try:
        container_registry_runs_list: List[Dict] = []
        for container_registry in container_registries_list:
            registry_runs_list = list(
                map(
                    lambda x: x.as_dict(),
                    client.runs.list(
                        registry_name=container_registry["name"],
                        resource_group_name=container_registry["resource_group"],
                    ),
                ),
            )
            for run in registry_runs_list:
                run["location"] = container_registry.get("location", "global")
                run["resource_group"] = get_azure_resource_group_name(run.get("id"))
                run["container_registry_id"] = run["id"][: run["id"].index("/runs")]
                run["consolelink"] = azure_console_link.get_console_link(
                    id=run["id"],
                    primary_ad_domain_name=common_job_parameters["Azure_Primary_AD_Domain_Name"],
                )
            container_registry_runs_list.extend(registry_runs_list)

        return container_registry_runs_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving container_registry_runs - {e}")
        return []


def _load_container_registry_runs_tx(
    tx: neo4j.Transaction,
    container_registry_runs_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_container_run = """
    UNWIND $container_registry_runs_list AS run
    MERGE (a:AzureContainerRegistryRun{id: run.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = run.type,
    a.location=run.location,
    a.region=run.location,
    a.consolelink = run.consolelink,
    a.resourcegroup = run.resource_group
    SET a.lastupdated = $update_tag,
    a.name = run.name
    WITH a,run
    MATCH (owner:AzureContainerRegistry{id: run.container_registry_id})
    MERGE (owner)-[r:CONTAIN]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_container_run,
        container_registry_runs_list=container_registry_runs_list,
        update_tag=update_tag,
    )
    for container_registry_run in container_registry_runs_list:
        resource_group = get_azure_resource_group_name(container_registry_run.get("id"))
        _attach_resource_group_container_registry_runs(tx, container_registry_run["id"], resource_group, update_tag)


def _attach_resource_group_container_registry_runs(
    tx: neo4j.Transaction, container_registry_run_id: str, resource_group: str, update_tag: int,
) -> None:
    ingest_container_run = """
    MATCH (a:AzureContainerRegistryRun{id: $run_id})
    WITH a
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (a)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_container_run,
        run_id=container_registry_run_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


def cleanup_container_registry_runs(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("azure_import_container_registry_runs_cleanup.json", neo4j_session, common_job_parameters)


def sync_container_registry_runs(
    neo4j_session: neo4j.Session,
    client: ContainerRegistryManagementClient,
    container_registries_list: List[Dict],
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    container_registry_runs_list = get_container_registry_runs_list(
        client,
        container_registries_list,
        common_job_parameters,
    )
    load_container_registry_runs(neo4j_session, container_registry_runs_list, update_tag)
    cleanup_container_registry_runs(neo4j_session, common_job_parameters)


@timeit
def get_container_registry_tasks_list(
    client: ContainerRegistryManagementClient,
    container_registries_list: List[Dict],
    common_job_parameters: Dict,
) -> List[Dict]:
    try:
        container_registry_tasks_list: List[Dict] = []
        for container_registry in container_registries_list:
            container_registry_tasks_list = container_registry_tasks_list + list(
                map(
                    lambda x: x.as_dict(),
                    client.runs.list(
                        registry_name=container_registry["name"],
                        resource_group_name=container_registry["resource_group"],
                    ),
                ),
            )

        for task in container_registry_tasks_list:
            task["resource_group"] = get_azure_resource_group_name(task.get("id"))
            task["container_registry_id"] = task["id"][: task["id"].index("/tasks")]
            task["consolelink"] = azure_console_link.get_console_link(
                id=task["id"],
                primary_ad_domain_name=common_job_parameters["Azure_Primary_AD_Domain_Name"],
            )

        return container_registry_tasks_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving container_registry_tasks - {e}")
        return []


def _load_container_registry_tasks_tx(
    tx: neo4j.Transaction,
    container_registry_tasks_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_container_task = """
    UNWIND $container_registry_tasks_list AS task
    MERGE (a:AzureContainerRegistryTask{id: task.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = task.type,
    a.location=task.location,
    a.region=task.location,
    a.conolelink = task.consolelink,
    a.resourcegroup = task.resource_group
    SET a.lastupdated = $update_tag,
    a.name = task.name
    WITH a,task
    MATCH (owner:AzureContainerRegistry{id: task.container_registry_id})
    MERGE (owner)-[r:CONTAIN]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_container_task,
        container_registry_tasks_list=container_registry_tasks_list,
        update_tag=update_tag,
    )
    for container_registry_task in container_registry_tasks_list:
        resource_group = get_azure_resource_group_name(container_registry_task.get("id"))
        _attach_resource_group_container_task(tx, container_registry_task["id"], resource_group, update_tag)


def _attach_resource_group_container_task(
    tx: neo4j.Transaction,
    container_registry_task_id: str,
    resource_group: str,
    update_tag: int,
) -> None:
    ingest_container_task = """
    MATCH (a:AzureContainerRegistryTask{id:$container_registry_task_id})
    WITH a
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (a)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_container_task,
        container_registry_task_id=container_registry_task_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


def cleanup_container_registry_tasks(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("azure_import_container_registry_tasks_cleanup.json", neo4j_session, common_job_parameters)


def sync_container_registry_tasks(
    neo4j_session: neo4j.Session,
    client: ContainerRegistryManagementClient,
    container_registries_list: List[Dict],
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    container_registry_tasks_list = get_container_registry_tasks_list(
        client,
        container_registries_list,
        common_job_parameters,
    )
    load_container_registry_tasks(neo4j_session, container_registry_tasks_list, update_tag)
    cleanup_container_registry_tasks(neo4j_session, common_job_parameters)


@timeit
def get_container_registry_webhooks_list(
    client: ContainerRegistryManagementClient,
    container_registries_list: List[Dict],
    common_job_parameters: Dict,
) -> List[Dict]:
    try:
        container_registry_webhooks_list: List[Dict] = []
        for container_registry in container_registries_list:
            container_registry_webhooks_list = container_registry_webhooks_list + list(
                map(
                    lambda x: x.as_dict(),
                    client.webhooks.list(
                        registry_name=container_registry["name"],
                        resource_group_name=container_registry["resource_group"],
                    ),
                ),
            )

        for webhook in container_registry_webhooks_list:
            webhook["resource_group"] = get_azure_resource_group_name(webhook.get("id"))
            webhook["container_registry_id"] = webhook["id"][: webhook["id"].index("/webhooks")]
            webhook["consolelink"] = azure_console_link.get_console_link(
                id=webhook["id"],
                primary_ad_domain_name=common_job_parameters["Azure_Primary_AD_Domain_Name"],
            )

        return container_registry_webhooks_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving container_registry_webhooks - {e}")
        return []


def _load_container_registry_webhooks_tx(
    tx: neo4j.Transaction,
    container_registry_webhooks_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_container_webhook = """
    UNWIND $container_registry_webhooks_list AS webhook
    MERGE (a:AzureContainerRegistryWebhook{id: webhook.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = webhook.type,
    a.location=webhook.location,
    a.region=webhook.location,
    a.consolelink = webhook.consolelink,
    a.resourcegroup = webhook.resource_group
    SET a.lastupdated = $update_tag,
    a.name = webhook.name
    WITH a,webhook
    MATCH (owner:AzureContainerRegistry{id: webhook.container_registry_id})
    MERGE (owner)-[r:CONTAIN]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_container_webhook,
        container_registry_webhooks_list=container_registry_webhooks_list,
        update_tag=update_tag,
    )
    for container_registry_webhook in container_registry_webhooks_list:
        resource_group = get_azure_resource_group_name(container_registry_webhook.get("id"))
        _attach_resource_group_container_registry_webhooks(
            tx, container_registry_webhook["id"], resource_group, update_tag,
        )


def _attach_resource_group_container_registry_webhooks(
    tx: neo4j.Transaction, container_registry_webhook_id: str, resource_group: str, update_tag: int,
) -> None:
    ingest_container_webhook = """
    MATCH (a:AzureContainerRegistryWebhook{id:$container_registry_webhook_id})
    WITH a
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (a)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_container_webhook,
        container_registry_webhook_id=container_registry_webhook_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


def cleanup_container_registry_webhooks(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("azure_import_container_registry_webhooks_cleanup.json", neo4j_session, common_job_parameters)


def sync_container_registry_webhooks(
    neo4j_session: neo4j.Session,
    client: ContainerRegistryManagementClient,
    container_registries_list: List[Dict],
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    container_registry_webhooks_list = get_container_registry_webhooks_list(
        client,
        container_registries_list,
        common_job_parameters,
    )
    load_container_registry_webhooks(neo4j_session, container_registry_webhooks_list, update_tag)
    cleanup_container_registry_webhooks(neo4j_session, common_job_parameters)


@timeit
def get_container_groups_list(
    client: ContainerInstanceManagementClient, regions: list, common_job_parameters: Dict,
) -> List[Dict]:
    try:
        container_groups_list = list(map(lambda x: x.as_dict(), client.container_groups.list()))
        group_data = []
        for group in container_groups_list:
            group["resource_group"] = get_azure_resource_group_name(group.get("id"))
            group["consolelink"] = azure_console_link.get_console_link(
                id=group["id"],
                primary_ad_domain_name=common_job_parameters["Azure_Primary_AD_Domain_Name"],
            )
            if regions is None:
                group_data.append(group)
            else:
                if group.get("location") in regions or group.get("location") == "global":
                    group_data.append(group)

        return group_data

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving Container Group - {e}")
        return []


def _load_container_groups_tx(
    tx: neo4j.Transaction,
    subscription_id: str,
    container_groups_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_container_group = """
    UNWIND $container_groups_list AS group
    MERGE (a:AzureContainerGroup{id: group.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = group.type,
    a.location = group.location,
    a.region = group.location,
    a.consolelink = group.consolelink,
    a.resourcegroup = group.resource_group
    SET a.lastupdated = $update_tag,
    a.name = group.name
    WITH a
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_container_group,
        container_groups_list=container_groups_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )
    for container_group in container_groups_list:
        resource_group = get_azure_resource_group_name(container_group.get("id"))
        _attach_resource_group_aks_container_group(tx, container_group["id"], resource_group, update_tag)


def _attach_resource_group_aks_container_group(
    tx: neo4j.Transaction,
    container_group_id: str,
    resource_group: str,
    update_tag: int,
) -> None:
    ingest_container_group = """
    MATCH (a:AzureContainerGroup{id: $group_id})
    WITH a
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (a)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_container_group,
        group_id=container_group_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


def cleanup_container_groups(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("azure_import_container_groups_cleanup.json", neo4j_session, common_job_parameters)


def sync_container_groups(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: Dict,
    regions: list,
) -> None:
    client = get_container_instance_Client(credentials, subscription_id)
    container_groups_list = get_container_groups_list(client, regions, common_job_parameters)

    load_container_groups(neo4j_session, subscription_id, container_groups_list, update_tag)
    cleanup_container_groups(neo4j_session, common_job_parameters)
    sync_containers(neo4j_session, container_groups_list, update_tag, common_job_parameters)


@timeit
def get_containers_list(container_groups_list: List[Dict]) -> List[Dict]:
    try:
        containers_list: List[Dict] = []
        for container_group in container_groups_list:
            for container in container_group.get("containers", []):
                container["id"] = f"{container_group.get('id', None)}/containers/{container.get('name', None)}"
                container["container_group_id"] = container_group["id"]
                container["resource_group"] = container_group["resource_group"]
                container["type"] = "Microsoft.ContainerInstance/containers"
                container["location"] = container_group.get("location", "global")

                containers_list.append(container)

        return containers_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving containers - {e}")
        return []


def _load_containers_tx(tx: neo4j.Transaction, containers_list: List[Dict], update_tag: int) -> None:
    ingest_container = """
    UNWIND $containers_list AS container
    MERGE (a:AzureContainer{id: container.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = container.type,
    a.name = container.name,
    a.location= container.location,
    a.region= container.location,
    a.resourcegroup = container.resource_group
    SET a.lastupdated = $update_tag
    WITH a,container
    MATCH (owner:AzureContainerGroup{id: container.container_group_id})
    MERGE (owner)-[r:CONTAIN]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_container,
        containers_list=containers_list,
        update_tag=update_tag,
    )
    for container in containers_list:
        resource_group = get_azure_resource_group_name(container.get("id"))
        _attach_resource_group_container(tx, container["id"], resource_group, update_tag)


def _attach_resource_group_container(
    tx: neo4j.Transaction, container_id: str, resource_group: str, update_tag: int,
) -> None:
    ingest_container = """
    MATCH (a:AzureContainer{id: $container_id})
    WITH a
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (a)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_container,
        container_id=container_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


def cleanup_containers(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("azure_import_containers_cleanup.json", neo4j_session, common_job_parameters)


def sync_containers(
    neo4j_session: neo4j.Session,
    container_groups_list: List[Dict],
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    containers_list = get_containers_list(container_groups_list)
    load_containers(neo4j_session, containers_list, update_tag)
    cleanup_containers(neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: Dict,
    regions: list,
) -> None:
    logger.info("Syncing AKS for subscription '%s'.", subscription_id)

    # paginator = common_job_parameters.get('paginator', None)

    # if not paginator.is_paginated():
    #     paginator.config = {
    #         "iteration": 0,
    #         "buckets": {
    #             "status": "PAGINATION_UNATTENDED",
    #             "totalItems": 0,
    #             "lastProcessedItem": 0
    #         }
    #     }

    sync_aks(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters, regions)
    sync_container_registries(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters, regions)
    # sync_container_groups(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters, regions)
