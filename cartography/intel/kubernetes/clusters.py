import json
import logging
from typing import Any

import neo4j
from kubernetes.client import WellKnownApi
from kubernetes.client.exceptions import ApiException
from kubernetes.client.models import V1Namespace
from kubernetes.client.models import VersionInfo

from cartography.client.core.tx import load
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import get_kubeconfig_tls_diagnostics
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.clusters import KubernetesClusterSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_kubernetes_cluster_namespace(client: K8sClient) -> V1Namespace:
    return client.core.read_namespace("kube-system")


@timeit
def get_kubernetes_cluster_version(client: K8sClient) -> VersionInfo:
    return client.version.get_code()


@timeit
def get_kubernetes_cluster_tls_diagnostics(client: K8sClient) -> dict[str, Any]:
    diagnostics = getattr(client, "tls_diagnostics", None)
    if isinstance(diagnostics, dict):
        return diagnostics
    return get_kubeconfig_tls_diagnostics(client.name, client.config_file)


def transform_kubernetes_cluster(
    client: K8sClient,
    namespace: V1Namespace,
    version: VersionInfo,
    tls_diagnostics: dict[str, Any],
) -> list[dict[str, Any]]:
    cluster = {
        "id": namespace.metadata.uid,
        "creation_timestamp": get_epoch(namespace.metadata.creation_timestamp),
        "external_id": client.external_id,
        "name": client.name,
        "git_version": version.git_version,
        "version_major": version.major,
        "version_minor": version.minor,
        "go_version": version.go_version,
        "compiler": version.compiler,
        "platform": version.platform,
    }
    cluster.update(tls_diagnostics)
    metadata = getattr(client, "gke_cluster", None)
    if isinstance(metadata, dict):
        cluster["gke_resource_name"] = metadata["resource_name"]
        cluster["gke_uid"] = metadata.get("id")
        cluster["workload_pool"] = (metadata.get("workloadIdentityConfig") or {}).get(
            "workloadPool"
        )

    return [cluster]


def load_kubernetes_cluster(
    neo4j_session: neo4j.Session,
    cluster_data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    logger.info(
        "Loading '{}' Kubernetes cluster into graph".format(cluster_data[0].get("name"))
    )
    load(
        neo4j_session,
        KubernetesClusterSchema(),
        cluster_data,
        lastupdated=update_tag,
    )


# cleaning up the kubernetes cluster node is currently not supported
# def cleanup(
#     neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
# ) -> None:
#     logger.debug("Running cleanup job for KubernetesCluster")
#     run_cleanup_job(
#         "kubernetes_cluster_cleanup.json", neo4j_session, common_job_parameters
#     )


def get_service_account_oidc(client: K8sClient) -> dict[str, str]:
    # Read the raw JSON: some Kubernetes client versions coerce this endpoint's
    # declared `str` response into a Python dict repr during deserialization.
    response = WellKnownApi(
        client.core.api_client
    ).get_service_account_issuer_open_id_configuration(_preload_content=False)
    try:
        discovery = json.loads(response.data)
    finally:
        response.release_conn()
    return {
        key: value
        for key, value in discovery.items()
        if key in ("issuer", "jwks_uri") and isinstance(value, str)
    }


@timeit
def sync_kubernetes_cluster(
    neo4j_session: neo4j.Session,
    client: K8sClient,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> dict[str, Any]:
    namespace = get_kubernetes_cluster_namespace(client)
    version = get_kubernetes_cluster_version(client)
    tls_diagnostics = get_kubernetes_cluster_tls_diagnostics(client)
    cluster_info = transform_kubernetes_cluster(
        client,
        namespace,
        version,
        tls_diagnostics,
    )

    if isinstance(getattr(client, "gke_cluster", None), dict):
        try:
            discovery = get_service_account_oidc(client)
            cluster_info[0]["service_account_issuer"] = discovery.get("issuer")
            cluster_info[0]["service_account_jwks_uri"] = discovery.get("jwks_uri")
        except ApiException as err:
            if err.status not in (401, 403, 404):
                raise
            logger.info(
                "Service account OIDC discovery is unavailable for this Kubernetes reader"
            )
    load_kubernetes_cluster(neo4j_session, cluster_info, update_tag)
    return cluster_info[0]
