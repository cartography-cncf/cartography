import logging
from contextlib import contextmanager
from typing import Iterator

import boto3
from neo4j import Session

from cartography.analysis.kubernetes.analysis import K8S_COMPUTE_ASSET_EXPOSURE_JOBS
from cartography.analysis.kubernetes.analysis import K8S_LB_EXPOSURE_JOBS
from cartography.config import Config
from cartography.intel.kubernetes import gke_auth
from cartography.intel.kubernetes.clusters import sync_kubernetes_cluster
from cartography.intel.kubernetes.eks import sync as sync_eks
from cartography.intel.kubernetes.gateway_api import sync_gateway_api
from cartography.intel.kubernetes.gke import sync as sync_gke
from cartography.intel.kubernetes.ingress import sync_ingress
from cartography.intel.kubernetes.namespaces import sync_namespaces
from cartography.intel.kubernetes.networkpolicies import sync_network_policies
from cartography.intel.kubernetes.nodes import sync_nodes
from cartography.intel.kubernetes.pods import sync_pods
from cartography.intel.kubernetes.rbac import sync_kubernetes_rbac
from cartography.intel.kubernetes.secrets import sync_secrets
from cartography.intel.kubernetes.services import sync_services
from cartography.intel.kubernetes.storage import sync_storage
from cartography.intel.kubernetes.util import get_k8s_clients
from cartography.intel.kubernetes.util import K8sClient
from cartography.intel.kubernetes.workloads import sync_workloads
from cartography.util import run_typed_analysis_job
from cartography.util import timeit

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


@contextmanager
def _gke_client(resource: str, config: Config) -> Iterator[K8sClient]:
    credentials = gke_auth.get_credentials(config.gke_impersonate_service_account)
    cluster = gke_auth.get_cluster(resource, credentials)
    with gke_auth.connect(cluster, credentials, config.gke_endpoint) as client:
        yield client


def _clients(config: Config) -> Iterator[K8sClient]:
    if config.k8s_kubeconfig:
        for client in get_k8s_clients(config.k8s_kubeconfig):
            if config.managed_kubernetes == "gke":
                credentials = gke_auth.get_credentials(
                    config.gke_impersonate_service_account
                )
                client.gke_cluster = gke_auth.get_cluster(
                    client.external_id or "", credentials
                )
            yield client
    for resource in getattr(config, "gke_clusters", None) or []:
        with _gke_client(resource, config) as client:
            yield client


@timeit
def start_k8s_ingestion(session: Session, config: Config) -> None:
    if not config.update_tag:
        logger.error("Cartography update tag not provided.")
        return

    if not config.k8s_kubeconfig and not getattr(config, "gke_clusters", None):
        logger.error("Provide a Kubernetes kubeconfig or --gke-cluster.")
        return

    common_job_parameters = {"UPDATE_TAG": config.update_tag}

    for client in _clients(config):
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
            sync_storage(session, client, config.update_tag, common_job_parameters)

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
            gateway_complete = sync_gateway_api(
                session, client, config.update_tag, common_job_parameters
            )
            sync_ingress(session, client, config.update_tag, common_job_parameters)

            gke_cluster = getattr(client, "gke_cluster", None)
            if isinstance(gke_cluster, dict):
                sync_gke(
                    session,
                    gke_cluster,
                    cluster_info["id"],
                    config.update_tag,
                    gateway_complete=gateway_complete is not False,
                )

            for job in K8S_COMPUTE_ASSET_EXPOSURE_JOBS:
                run_typed_analysis_job(job, session, common_job_parameters)
            for job in K8S_LB_EXPOSURE_JOBS:
                run_typed_analysis_job(job, session, common_job_parameters)
        except Exception:
            logger.exception(f"Failed to sync data for k8s cluster {client.name}...")
            raise
