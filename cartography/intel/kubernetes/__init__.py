import logging

from neo4j import Session

from cartography.analysis.kubernetes.analysis import K8S_COMPUTE_ASSET_EXPOSURE_JOBS
from cartography.analysis.kubernetes.analysis import K8S_LB_EXPOSURE_JOBS
from cartography.config import Config
from cartography.util import run_typed_analysis_job
from cartography.util import timeit
from cartography.util.lazy import lazy_callable
from cartography.util.lazy import lazy_import

# Bound lazily so that the provider SDK only loads once the config gate below
# has decided that this module has something to sync.
boto3 = lazy_import("boto3")
get_k8s_clients = lazy_callable("cartography.intel.kubernetes.util", "get_k8s_clients")
sync_eks = lazy_callable("cartography.intel.kubernetes.eks", "sync")
sync_gateway_api = lazy_callable(
    "cartography.intel.kubernetes.gateway_api", "sync_gateway_api"
)
sync_ingress = lazy_callable("cartography.intel.kubernetes.ingress", "sync_ingress")
sync_kubernetes_cluster = lazy_callable(
    "cartography.intel.kubernetes.clusters", "sync_kubernetes_cluster"
)
sync_kubernetes_rbac = lazy_callable(
    "cartography.intel.kubernetes.rbac", "sync_kubernetes_rbac"
)
sync_namespaces = lazy_callable(
    "cartography.intel.kubernetes.namespaces", "sync_namespaces"
)
sync_network_policies = lazy_callable(
    "cartography.intel.kubernetes.networkpolicies", "sync_network_policies"
)
sync_nodes = lazy_callable("cartography.intel.kubernetes.nodes", "sync_nodes")
sync_pods = lazy_callable("cartography.intel.kubernetes.pods", "sync_pods")
sync_secrets = lazy_callable("cartography.intel.kubernetes.secrets", "sync_secrets")
sync_services = lazy_callable("cartography.intel.kubernetes.services", "sync_services")
sync_workloads = lazy_callable(
    "cartography.intel.kubernetes.workloads", "sync_workloads"
)

logger = logging.getLogger(__name__)


def get_region_from_arn(arn: str) -> str:
    """
    Extract AWS region from EKS cluster ARN.
    Example: arn:aws:eks:us-east-1:111122223333:cluster/example-eks-cluster → us-east-1
    """
    parts = arn.split(":")
    if len(parts) < 6 or parts[2] != "eks":
        raise ValueError(f"Invalid EKS cluster ARN: {arn}")
    return parts[3]


@timeit
def start_k8s_ingestion(session: Session, config: Config) -> None:
    if not config.update_tag:
        logger.error("Cartography update tag not provided.")
        return

    if not config.k8s_kubeconfig:
        logger.error("Kubernetes kubeconfig not provided.")
        return

    common_job_parameters = {"UPDATE_TAG": config.update_tag}

    for client in get_k8s_clients(config.k8s_kubeconfig):
        logger.info(f"Syncing data for k8s cluster {client.name}...")
        try:
            cluster_info = sync_kubernetes_cluster(
                session,
                client,
                config.update_tag,
                common_job_parameters,
            )
            common_job_parameters["CLUSTER_ID"] = cluster_info.get("id")
            cluster_external_ref = cluster_info.get("external_id") or cluster_info.get(
                "name", ""
            )

            sync_namespaces(session, client, config.update_tag, common_job_parameters)
            node_arch_map = sync_nodes(
                session, client, config.update_tag, common_job_parameters
            )
            sync_kubernetes_rbac(
                session, client, config.update_tag, common_job_parameters
            )
            # Sync workload controllers before pods so the pod sync can collapse
            # Pod -> ReplicaSet -> Deployment using the returned RS->Deployment map.
            replicaset_owner_map = sync_workloads(
                session, client, config.update_tag, common_job_parameters
            )

            # Extract region from cluster ARN (works for EKS; None for non-EKS clusters)
            region: str | None = None
            if config.managed_kubernetes == "eks":
                # EKS clusters always have a valid ARN — let ValueError propagate if not
                region = get_region_from_arn(cluster_external_ref)
                boto3_session = boto3.Session()
                sync_eks(
                    session,
                    client,
                    boto3_session,
                    region,
                    config.update_tag,
                    cluster_info.get("id", ""),
                    cluster_external_ref,
                )
            else:
                try:
                    region = get_region_from_arn(cluster_external_ref)
                except ValueError:
                    pass
            all_pods = sync_pods(
                session,
                client,
                config.update_tag,
                common_job_parameters,
                region=region,
                node_arch_map=node_arch_map,
                replicaset_owner_map=replicaset_owner_map,
            )
            sync_secrets(session, client, config.update_tag, common_job_parameters)
            sync_services(
                session,
                client,
                all_pods,
                config.update_tag,
                common_job_parameters,
            )
            sync_network_policies(
                session,
                client,
                all_pods,
                config.update_tag,
                common_job_parameters,
            )
            sync_gateway_api(session, client, config.update_tag, common_job_parameters)
            sync_ingress(session, client, config.update_tag, common_job_parameters)

            for job in K8S_COMPUTE_ASSET_EXPOSURE_JOBS:
                run_typed_analysis_job(job, session, common_job_parameters)
            for job in K8S_LB_EXPOSURE_JOBS:
                run_typed_analysis_job(job, session, common_job_parameters)
        except Exception:
            logger.exception(f"Failed to sync data for k8s cluster {client.name}...")
            raise
