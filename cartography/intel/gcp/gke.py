import json
import logging
import time
from typing import Dict
from typing import List

import neo4j
from cloudconsolelink.clouds.gcp import GCPLinker
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from . import label
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
gcp_console_link = GCPLinker()


@timeit
def get_gke_clusters(container: Resource, project_id: str, regions: list, common_job_parameters) -> List[Dict]:
    """
    Returns a processed list of GKE cluster dicts for the given project.

    :type container: The GCP Container resource object
    :param container: The Container resource object created by googleapiclient.discovery.build()
    :type project_id: str
    :param project_id: The Google Project Id that you are retrieving clusters from
    :rtype: List[Dict]
    :return: List of processed cluster dicts, each with 'id' and 'region' pre-set.
    """
    try:
        req = container.projects().zones().clusters().list(projectId=project_id, zone="-")
        res = req.execute()
        data = []
        for item in res.get("clusters", []):
            item["region"] = get_region_from_location(item["location"])
            item["id"] = f"projects/{project_id}/locations/{item['region']}/clusters/{item['name']}"
            item["consolelink"] = gcp_console_link.get_console_link(
                resource_name="gke_cluster",
                project_id=project_id,
                zone=item["zone"],
                gke_cluster_name=item["name"],
            )
            if regions is None or len(regions) == 0:
                data.append(item)
            else:
                if get_region_from_location(item["zone"]) in regions:
                    data.append(item)

        return data
    except HttpError as e:
        err = json.loads(e.content.decode("utf-8"))["error"]
        if err["status"] == "PERMISSION_DENIED":
            logger.warning(
                ("Could not retrieve GKE clusters on project %s due to permissions issue. Code: %s, Message: %s"),
                project_id,
                err["code"],
                err["message"],
            )
            return []
        else:
            raise


def get_region_from_location(location):
    if not location:
        return location

    location = location.lower()
    sections = location.split("-")

    if len(sections) > 2:
        return location[: location.index("-", location.index("-") + 1)]

    else:
        return location


@timeit
def load_gke_clusters(
    neo4j_session: neo4j.Session, cluster_resp: List[Dict], project_id: str, gcp_update_tag: int,
) -> None:
    """
    Ingest GCP GKE Clusters to Neo4j.

    :type neo4j_session: neo4j.Session
    :param neo4j_session: The Neo4j session object
    :type cluster_resp: List[Dict]
    :param cluster_resp: Processed cluster list from get_gke_clusters()
    :type project_id: str
    :param project_id: The GCP project ID
    :type gcp_update_tag: int
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :rtype: NoneType
    :return: Nothing
    """
    query = """
    MERGE (cluster:GKECluster{id: $ClusterId})
    ON CREATE SET
        cluster.firstseen = timestamp(),
        cluster.created_at = $ClusterCreateTime
    SET
        cluster.name = $ClusterName,
        cluster.self_link = $ClusterSelfLink,
        cluster.description = $ClusterDescription,
        cluster.logging_service = $ClusterLoggingService,
        cluster.monitoring_service = $ClusterMonitoringService,
        cluster.network = $ClusterNetwork,
        cluster.subnetwork = $ClusterSubnetwork,
        cluster.cluster_ipv4cidr = $ClusterIPv4Cidr,
        cluster.zone = $ClusterZone,
        cluster.region = $ClusterRegion,
        cluster.location = $ClusterLocation,
        cluster.endpoint = $ClusterEndpoint,
        cluster.initial_version = $ClusterInitialVersion,
        cluster.current_master_version = $ClusterMasterVersion,
        cluster.status = $ClusterStatus,
        cluster.services_ipv4cidr = $ClusterServicesIPv4Cidr,
        cluster.database_encryption = $ClusterDatabaseEncryption,
        cluster.network_policy = $ClusterNetworkPolicy,
        cluster.master_authorized_networks = $ClusterMasterAuthorizedNetworks,
        cluster.masterGlobalAccessConfig = $ClusterMasterGlobalAccessConfig,
        cluster.legacy_abac = $ClusterAbac,
        cluster.shielded_nodes = $ClusterShieldedNodes,
        cluster.private_nodes = $ClusterPrivateNodes,
        cluster.private_endpoint_enabled = $ClusterPrivateEndpointEnabled,
        cluster.private_endpoint = $ClusterPrivateEndpoint,
        cluster.public_endpoint = $ClusterPublicEndpoint,
        cluster.masterauth_username = $ClusterMasterUsername,
        cluster.consolelink = $consolelink,
        cluster.masterauth_password = $ClusterMasterPassword,
        cluster.enable_kubernetes_alpha = $ClusterKubernetesAlpha,
        cluster.lastupdated = $gcp_update_tag
    WITH cluster
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(cluster)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    for cluster in cluster_resp:
        cluster["region"] = get_region_from_location(cluster.get("location"))

        neo4j_session.run(
            query,
            ProjectId=project_id,
            ClusterId=cluster["id"],
            ClusterSelfLink=cluster["selfLink"],
            ClusterCreateTime=cluster["createTime"],
            ClusterName=cluster["name"],
            ClusterDescription=cluster.get("description"),
            ClusterLoggingService=cluster.get("loggingService"),
            ClusterMonitoringService=cluster.get("monitoringService"),
            ClusterNetwork=cluster.get("network"),
            ClusterSubnetwork=cluster.get("subnetwork"),
            ClusterIPv4Cidr=cluster.get("clusterIpv4Cidr"),
            ClusterZone=cluster.get("zone"),
            ClusterRegion=cluster.get("region"),
            ClusterLocation=cluster.get("location"),
            ClusterEndpoint=cluster.get("endpoint"),
            ClusterInitialVersion=cluster.get("initialClusterVersion"),
            ClusterMasterVersion=cluster.get("currentMasterVersion"),
            ClusterStatus=cluster.get("status"),
            ClusterServicesIPv4Cidr=cluster.get("servicesIpv4Cidr"),
            ClusterDatabaseEncryption=cluster.get("databaseEncryption", {}).get("state"),
            ClusterNetworkPolicy=_process_network_policy(cluster),
            ClusterMasterAuthorizedNetworks=cluster.get("masterAuthorizedNetworksConfig", {}).get("enabled", False),
            ClusterAbac=cluster.get("legacyAbac", {}).get("enabled"),
            ClusterShieldedNodes=cluster.get("shieldedNodes", {}).get("enabled"),
            ClusterPrivateNodes=cluster.get("privateClusterConfig", {}).get("enablePrivateNodes"),
            ClusterPrivateEndpointEnabled=cluster.get("privateClusterConfig", {}).get("enablePrivateEndpoint"),
            ClusterPrivateEndpoint=cluster.get("privateClusterConfig", {}).get("privateEndpoint"),
            ClusterMasterGlobalAccessConfig=cluster.get("privateClusterConfig", {})
            .get("masterGlobalAccessConfig", {})
            .get("enabled"),
            ClusterPublicEndpoint=cluster.get("privateClusterConfig", {}).get("publicEndpoint"),
            ClusterMasterUsername=cluster.get("masterAuth", {}).get("username"),
            ClusterMasterPassword=cluster.get("masterAuth", {}).get("password"),
            ClusterKubernetesAlpha=cluster.get("enableKubernetesAlpha", False),
            consolelink=cluster.get("consolelink"),
            gcp_update_tag=gcp_update_tag,
        )


@timeit
def load_gke_node_pools(
    neo4j_session: neo4j.Session,
    clusters: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Ingest GKE NodePool nodes to Neo4j and create HAS_NODE_POOL edges from GKECluster.

    Must be called AFTER load_gke_clusters so that GKECluster nodes already exist
    for the MATCH inside the write transaction.

    NodePool ID format:
        projects/{project_id}/locations/{region}/clusters/{cluster_name}/nodePools/{pool_name}

    :type neo4j_session: neo4j.Session
    :param neo4j_session: The Neo4j session object
    :type clusters: List[Dict]
    :param clusters: Processed cluster list from get_gke_clusters(). Each dict must
                     have an "id" key (set by get_gke_clusters) and a "nodePools" list.
    :type project_id: str
    :param project_id: The GCP project ID (used only for logging)
    :type gcp_update_tag: int
    :param gcp_update_tag: Timestamp to stamp on all upserted nodes and relationships
    :rtype: NoneType
    :return: Nothing
    """
    # Flatten nodePools from all clusters into one list. Doing this in Python keeps
    # the Cypher simple; the write transaction just UNWINDs the resulting records.
    pool_records = []
    for cluster in clusters:
        cluster_id = cluster["id"]
        for pool in cluster.get("nodePools", []):
            config = pool.get("config", {})
            pool_records.append(
                {
                    "id": f"{cluster_id}/nodePools/{pool['name']}",
                    "cluster_id": cluster_id,
                    "name": pool["name"],
                    "status": pool.get("status"),
                    "version": pool.get("version"),
                    "initial_node_count": pool.get("initialNodeCount"),
                    "machine_type": config.get("machineType"),
                    "disk_size_gb": config.get("diskSizeGb"),
                    "image_type": config.get("imageType"),
                    "disk_type": config.get("diskType"),
                    "auto_repair": pool.get("management", {}).get("autoRepair"),
                    "max_pods_per_node": pool.get("maxPodsConstraint", {}).get("maxPodsPerNode"),
                    "self_link": pool.get("selfLink"),
                },
            )

    if not pool_records:
        logger.debug("No node pools found for project %s; skipping node pool load.", project_id)
        return

    logger.info("Loading %d GKE node pools for project %s.", len(pool_records), project_id)
    neo4j_session.write_transaction(_load_gke_node_pools_tx, pool_records, gcp_update_tag)


def _load_gke_node_pools_tx(tx: neo4j.Transaction, pool_records: List[Dict], gcp_update_tag: int) -> None:
    """
    Write transaction for load_gke_node_pools.

    Uses UNWIND to batch-insert all pool records in a single round-trip and then
    creates HAS_NODE_POOL edges to the parent GKECluster nodes.

    The 'WITH p, pool' after the MERGE preserves both the new node and the original
    record dict so that pool.cluster_id is still accessible for the final MATCH.
    """
    query = """
    UNWIND $PoolRecords AS pool
    MERGE (p:GKENodePool{id: pool.id})
    ON CREATE SET p.firstseen = timestamp()
    SET
        p.name = pool.name,
        p.cluster_id = pool.cluster_id,
        p.status = pool.status,
        p.version = pool.version,
        p.initial_node_count = pool.initial_node_count,
        p.machine_type = pool.machine_type,
        p.disk_size_gb = pool.disk_size_gb,
        p.image_type = pool.image_type,
        p.disk_type = pool.disk_type,
        p.auto_repair = pool.auto_repair,
        p.max_pods_per_node = pool.max_pods_per_node,
        p.self_link = pool.self_link,
        p.lastupdated = $gcp_update_tag
    WITH p, pool
    MATCH (cluster:GKECluster{id: pool.cluster_id})
    MERGE (cluster)-[r:HAS_NODE_POOL]->(p)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(query, PoolRecords=pool_records, gcp_update_tag=gcp_update_tag)


def _process_network_policy(cluster: Dict) -> bool:
    """
    Parse cluster.networkPolicy to verify if
    the provider has been enabled.
    """
    provider = cluster.get("networkPolicy", {}).get("provider")
    enabled = cluster.get("networkPolicy", {}).get("enabled")
    if provider and enabled is True:
        return provider
    return False


@timeit
def cleanup_gke_clusters(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date GCP GKE Clusters nodes and relationships.

    :type neo4j_session: neo4j.Session
    :param neo4j_session: The Neo4j session
    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j
    :rtype: NoneType
    :return: Nothing
    """
    run_cleanup_job("gcp_gke_cluster_cleanup.json", neo4j_session, common_job_parameters)


@timeit
def cleanup_gke_node_pools(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date GKE NodePool nodes and their HAS_NODE_POOL relationships.

    :type neo4j_session: neo4j.Session
    :param neo4j_session: The Neo4j session
    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j
    :rtype: NoneType
    :return: Nothing
    """
    run_cleanup_job("gcp_gke_node_pool_cleanup.json", neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    container: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
    regions: list,
) -> None:
    """
    Get GCP GKE Clusters and NodePools, ingest to Neo4j, and clean up stale data.

    :type neo4j_session: neo4j.Session
    :param neo4j_session: The Neo4j session
    :type container: Resource
    :param container: The Container resource object created by googleapiclient.discovery.build()
    :type project_id: str
    :param project_id: The project ID of the corresponding project
    :type gcp_update_tag: int
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j
    :rtype: NoneType
    :return: Nothing
    """
    tic = time.perf_counter()

    logger.info("Syncing GKE for project '%s', at %s.", project_id, tic)

    gke_res = get_gke_clusters(container, project_id, regions, common_job_parameters)

    # Clusters must be loaded before node pools so that GKECluster nodes
    # already exist when load_gke_node_pools does MATCH (cluster:GKECluster{...}).
    load_gke_clusters(neo4j_session, gke_res, project_id, gcp_update_tag)
    load_gke_node_pools(neo4j_session, gke_res, project_id, gcp_update_tag)

    # TODO scope the cleanup to the current project - https://github.com/lyft/cartography/issues/381
    cleanup_gke_clusters(neo4j_session, common_job_parameters)
    cleanup_gke_node_pools(neo4j_session, common_job_parameters)
    label.sync_labels(neo4j_session, gke_res, gcp_update_tag, common_job_parameters, "gke clusters", "GKECluster")

    toc = time.perf_counter()
    logger.info(f"Time to process GKE: {toc - tic:0.4f} seconds")
