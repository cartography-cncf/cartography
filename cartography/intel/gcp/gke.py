import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.gke_utils import GKEClusterRef
from cartography.intel.gcp.gke_utils import parse_cluster_ref
from cartography.intel.gcp.labels import sync_labels
from cartography.intel.gcp.util import classify_gcp_http_error
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import summarize_gcp_http_error
from cartography.models.gcp.gke import GCPGKEClusterSchema
from cartography.models.gcp.gke import GKENodePoolSchema
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
        res = gcp_api_execute_with_retry(req)
        for cluster in res.get("clusters", []):
            # selfLink may carry the project number; key on the project ID instead so
            # Kubernetes-side lookups (`--gke-cluster projects/PROJECT_ID/...`) match.
            reference = parse_cluster_ref(cluster["selfLink"])
            cluster["resource_name"] = GKEClusterRef(
                project_id, reference.location, reference.name
            ).resource_name
        return res
    except HttpError as e:
        if classify_gcp_http_error(e) in (
            "api_disabled",
            "billing_disabled",
            "forbidden",
        ):
            logger.warning(
                "Could not retrieve GKE clusters on project %s due to permissions issue. %s",
                project_id,
                summarize_gcp_http_error(e),
            )
            # Returning empty results on permission/API-disabled errors is intentional:
            # it allows the cleanup step to remove previously ingested data when access
            # to this project is lost, so the graph reflects only the current visible state.
            return {}
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


def _process_network_policy(cluster: Dict) -> str | bool:
    """
    Parse cluster.networkPolicy to verify if
    the provider has been enabled.
    """
    if cluster.get("networkConfig", {}).get("datapathProvider") == "ADVANCED_DATAPATH":
        return "DATAPLANE_V2"
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
    GraphJob.from_node_schema(GKENodePoolSchema(), common_job_parameters).run(
        neo4j_session,
    )
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
    project_number: str | None = None,
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
    clusters = transform_gke_clusters(gke_res)
    if clusters:
        load(
            neo4j_session,
            GCPGKEClusterSchema(),
            clusters,
            lastupdated=gcp_update_tag,
            PROJECT_ID=project_id,
        )
    node_pools = transform_node_pools(gke_res, project_number)
    if node_pools:
        load(
            neo4j_session,
            GKENodePoolSchema(),
            node_pools,
            lastupdated=gcp_update_tag,
            PROJECT_ID=project_id,
        )
    if gke_res.get("missingZones"):
        # An unreachable zone is not an empty zone: keep clusters we could not see.
        # Label sync also cleans up, so it waits for a complete listing too.
        logger.warning(
            "GKE cluster listing for project %s is missing zones %s; skipping "
            "label sync and cleanup.",
            project_id,
            gke_res["missingZones"],
        )
        return
    sync_labels(
        neo4j_session,
        clusters,
        "gke_cluster",
        project_id,
        gcp_update_tag,
        common_job_parameters,
    )
    cleanup_gke_clusters(neo4j_session, common_job_parameters)


def _transform_control_plane_endpoints(cluster: Dict[str, Any]) -> Dict[str, Any]:
    """
    Describe how clients can reach the GKE control plane (the Kubernetes API server).

    `controlPlaneEndpointsConfig` supersedes `privateClusterConfig`: the DNS endpoint is
    reachable from the internet when `allowExternalTraffic` is true (authorized by IAM
    `container.clusters.connect`), and IP endpoints can be disabled entirely. Older
    responses without it fall back to `privateClusterConfig.enablePrivateEndpoint`.
    """
    endpoints = cluster.get("controlPlaneEndpointsConfig")
    if not endpoints:
        private_endpoint = (cluster.get("privateClusterConfig") or {}).get(
            "enablePrivateEndpoint"
        )
        return {
            "dns_endpoint": None,
            "dns_endpoint_enabled": None,
            "dns_allow_kubernetes_tokens": None,
            "dns_allow_kubernetes_certs": None,
            "ip_endpoints_enabled": None,
            "public_ip_endpoint_enabled": None,
            "control_plane_public_access": not private_endpoint,
        }
    dns = endpoints.get("dnsEndpointConfig")
    ip = endpoints.get("ipEndpointsConfig")
    dns_enabled = bool(dns.get("allowExternalTraffic")) if dns is not None else None
    ip_enabled = bool(ip.get("enabled")) if ip is not None else None
    public_ip_enabled = (
        bool(ip.get("enabled") and ip.get("enablePublicEndpoint"))
        if ip is not None
        else None
    )
    return {
        "dns_endpoint": (dns or {}).get("endpoint"),
        "dns_endpoint_enabled": dns_enabled,
        "dns_allow_kubernetes_tokens": (
            bool(dns.get("enableK8sTokensViaDns")) if dns is not None else None
        ),
        "dns_allow_kubernetes_certs": (
            bool(dns.get("enableK8sCertsViaDns")) if dns is not None else None
        ),
        "ip_endpoints_enabled": ip_enabled,
        "public_ip_endpoint_enabled": public_ip_enabled,
        "control_plane_public_access": bool(dns_enabled or public_ip_enabled),
    }


def transform_gke_clusters(api_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Transform GKE API response into a list of dicts suitable for the data model loader.
    """
    result: List[Dict[str, Any]] = []
    for c in api_result.get("clusters", []):
        ref = parse_cluster_ref(c.get("resource_name") or c["selfLink"])
        transformed: Dict[str, Any] = {
            # Required fields
            "id": c["selfLink"],
            "resource_name": ref.resource_name,
            "project_id": ref.project,
            "gke_uid": c.get("id"),
            "autopilot_enabled": (c.get("autopilot") or {}).get("enabled", False),
            "workload_pool": (c.get("workloadIdentityConfig") or {}).get(
                "workloadPool"
            ),
            "datapath_provider": (c.get("networkConfig") or {}).get("datapathProvider"),
            **_transform_control_plane_endpoints(c),
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
            "workload_identity_enabled": bool(
                (c.get("workloadIdentityConfig", {}) or {}).get("workloadPool"),
            ),
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
            "resourceLabels": c.get("resourceLabels", {}),
        }
        result.append(transformed)
    return result


def transform_node_pools(
    api_result: Dict[str, Any],
    project_number: str | None = None,
) -> list[dict[str, Any]]:
    """
    Transform the `nodePools` of each cluster in a GKE API response. GKE reports the
    Compute Engine default service account as `default`; resolve it to its email when
    the project number is known so the node pool links to the account.
    """
    default_account = (
        f"{project_number}-compute@developer.gserviceaccount.com"
        if project_number
        else None
    )
    pools = []
    for cluster in api_result.get("clusters", []):
        ref = parse_cluster_ref(cluster.get("resource_name") or cluster["selfLink"])
        for pool in cluster.get("nodePools", []):
            config = pool.get("config") or {}
            pools.append(
                {
                    "id": f"{ref.resource_name}/nodePools/{pool['name']}",
                    "name": pool["name"],
                    "cluster_id": cluster["selfLink"],
                    "cluster_resource_name": ref.resource_name,
                    "service_account": (
                        default_account
                        if config.get("serviceAccount") in (None, "default")
                        else config.get("serviceAccount")
                    ),
                    "oauth_scopes": config.get("oauthScopes"),
                    "workload_metadata_mode": (
                        config.get("workloadMetadataConfig") or {}
                    ).get("mode"),
                    "instance_group_urls": pool.get("instanceGroupUrls"),
                    "status": pool.get("status"),
                    "version": pool.get("version"),
                }
            )
    return pools
