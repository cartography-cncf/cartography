import json
import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.gke import GCPGKEClusterSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gke_clusters(container: Resource, project_id: str) -> Dict:
    """
    Returns a GCP response object containing a list of GKE clusters within the given project.

    :type container: The GCP Container resource object
    :param container: The Container resource object created by googleapiclient.discovery.build()

    :type project_id: str
    :param project_id: The Google Project Id that you are retrieving clusters from

    :rtype: Cluster Object
    :return: Cluster response object
    """
    try:
        req = (
            container.projects().zones().clusters().list(projectId=project_id, zone="-")
        )
        res = req.execute()
        return res
    except HttpError as e:
        err = json.loads(e.content.decode("utf-8"))["error"]
        if err["status"] == "PERMISSION_DENIED":
            logger.warning(
                (
                    "Could not retrieve GKE clusters on project %s due to permissions issue. Code: %s, Message: %s"
                ),
                project_id,
                err["code"],
                err["message"],
            )
            return {}
        else:
            raise


@timeit
def load_gke_clusters(
    neo4j_session: neo4j.Session,
    cluster_resp: Dict,
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Ingest GCP GKE clusters using the data model loader.
    """
    clusters: List[Dict[str, Any]] = transform_gke_clusters(cluster_resp)

    if not clusters:
        return

    load(
        neo4j_session,
        GCPGKEClusterSchema(),
        clusters,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


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
def cleanup_gke_clusters(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Scoped cleanup for GKE clusters based on the project sub-resource relationship.
    """
    GraphJob.from_node_schema(GCPGKEClusterSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_gke_clusters(
    neo4j_session: neo4j.Session,
    container: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Get GCP GKE Clusters using the Container resource object, ingest to Neo4j, and clean up old data.

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type container: The Container resource object created by googleapiclient.discovery.build()
    :param container: The GCP Container resource object

    :type project_id: str
    :param project_id: The project ID of the corresponding project

    :type gcp_update_tag: timestamp
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    logger.info("Syncing GKE clusters for project %s.", project_id)
    gke_res = get_gke_clusters(container, project_id)
    load_gke_clusters(neo4j_session, gke_res, project_id, gcp_update_tag)
    cleanup_gke_clusters(neo4j_session, common_job_parameters)


def transform_gke_clusters(api_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Transform GKE API response into a list of dicts suitable for the data model loader.
    """
    result: List[Dict[str, Any]] = []
    for c in api_result.get("clusters", []):
        transformed: Dict[str, Any] = {
            # Required fields
            "id": c["selfLink"],
            "self_link": c["selfLink"],
            "name": c["name"],
            "created_at": c.get("createTime"),
            # Optional fields
            "description": c.get("description"),
            "logging_service": c.get("loggingService"),
            "monitoring_service": c.get("monitoringService"),
            "network": c.get("network"),
            "subnetwork": c.get("subnetwork"),
            "cluster_ipv4cidr": c.get("clusterIpv4Cidr"),
            "zone": c.get("zone"),
            "location": c.get("location"),
            "endpoint": c.get("endpoint"),
            "initial_version": c.get("initialClusterVersion"),
            "current_master_version": c.get("currentMasterVersion"),
            "status": c.get("status"),
            "services_ipv4cidr": c.get("servicesIpv4Cidr"),
            "database_encryption": (c.get("databaseEncryption", {}) or {}).get("state"),
            "network_policy": _process_network_policy(c),
            "master_authorized_networks": (
                c.get("masterAuthorizedNetworksConfig", {}) or {}
            ).get("enabled"),
            "legacy_abac": (c.get("legacyAbac", {}) or {}).get("enabled"),
            "shielded_nodes": (c.get("shieldedNodes", {}) or {}).get("enabled"),
            "private_nodes": (c.get("privateClusterConfig", {}) or {}).get(
                "enablePrivateNodes"
            ),
            "private_endpoint_enabled": (c.get("privateClusterConfig", {}) or {}).get(
                "enablePrivateEndpoint"
            ),
            "private_endpoint": (c.get("privateClusterConfig", {}) or {}).get(
                "privateEndpoint"
            ),
            "public_endpoint": (c.get("privateClusterConfig", {}) or {}).get(
                "publicEndpoint"
            ),
            "masterauth_username": (c.get("masterAuth", {}) or {}).get("username"),
            "masterauth_password": (c.get("masterAuth", {}) or {}).get("password"),
        }
        result.append(transformed)
    return result
