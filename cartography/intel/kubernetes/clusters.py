import logging
from typing import Any

import neo4j
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

    load_kubernetes_cluster(neo4j_session, cluster_info, update_tag)
    return cluster_info[0]
