import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.cluster import KubernetesClusterSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_kubernetes_cluster_namespace(client: K8sClient) -> Dict[str, Any]:
    ns = client.core.read_namespace("kube-system")
    namespace = {
        "id": ns.metadata.uid,
        "creation_timestamp": get_epoch(ns.metadata.creation_timestamp),
    }
    return namespace


@timeit
def get_kubernetes_cluster_version(client: K8sClient) -> Dict[str, Any]:
    v = client.version.get_code()
    version = {
        "major": v.major,
        "minor": v.minor,
        "git_version": v.git_version,
        "go_version": v.go_version,
        "compiler": v.compiler,
        "platform": v.platform,
    }
    return version


def transform_kubernetes_cluster(client: K8sClient, namespace: Dict, version: Dict) -> List[Dict[str, Any]]:
    cluster = dict()
    cluster["id"] = namespace.get("id")
    cluster["creation_timestamp"] = namespace.get("creation_timestamp")
    cluster["external_id"] = client.external_id
    cluster["name"] = client.name
    cluster["git_version"] = version.get("git_version")
    cluster["version_major"] = version.get("major")
    cluster["version_minor"] = version.get("minor")
    cluster["go_version"] = version.get("go_version")
    cluster["compiler"] = version.get("compiler")
    cluster["platform"] = version.get("platform")

    return [cluster]


def load_kubernetes_cluster(
        neo4j_session: neo4j.Session,
        cluster_data: List[Dict[str, Any]],
        update_tag: int,
) -> None:
    logger.info("Loading '{}' Kubernetes cluster into graph".format(cluster_data[0].get("name")))
    load(
        neo4j_session,
        KubernetesClusterSchema(),
        cluster_data,
        lastupdated=update_tag,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    # Cleanup logic can be added here if needed
    logger.debug("Running cleanup job for KubernetesCluster")
    cleanup_job = GraphJob.from_node_schema(KubernetesClusterSchema(), common_job_parameters)
    cleanup_job.run(neo4j_session)


@timeit
def sync_kubernetes_cluster(
        neo4j_session: neo4j.Session,
        client: K8sClient,
        update_tag: int,
        common_job_parameters: Dict[str, Any],
) -> Dict[str, Any]:
    namespace = get_kubernetes_cluster_namespace(client)
    version = get_kubernetes_cluster_version(client)
    cluster_info = transform_kubernetes_cluster(client, namespace, version)

    load_kubernetes_cluster(neo4j_session, cluster_info, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return cluster_info[0]
