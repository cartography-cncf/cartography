import logging
from typing import Any

import neo4j
from kubernetes.client.models import V1Node

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.container_arch import normalize_architecture
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import k8s_paginate
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.nodes import KubernetesNodeSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_nodes(client: K8sClient) -> list[V1Node]:
    return k8s_paginate(client.core.list_node)


def transform_nodes(nodes: list[V1Node]) -> list[dict[str, Any]]:
    transformed_nodes = []
    for node in nodes:
        ready = None
        if node.status and node.status.conditions:
            for condition in node.status.conditions:
                if condition.type == "Ready":
                    ready = condition.status == "True"
                    break

        architecture_raw = None
        if node.status and node.status.node_info:
            architecture_raw = node.status.node_info.architecture

        transformed_nodes.append(
            {
                "uid": node.metadata.uid,
                "name": node.metadata.name,
                "creation_timestamp": get_epoch(node.metadata.creation_timestamp),
                "deletion_timestamp": get_epoch(node.metadata.deletion_timestamp),
                "architecture": normalize_architecture(architecture_raw),
                "operating_system": (
                    node.status.node_info.operating_system
                    if node.status and node.status.node_info
                    else None
                ),
                "os_image": (
                    node.status.node_info.os_image
                    if node.status and node.status.node_info
                    else None
                ),
                "kernel_version": (
                    node.status.node_info.kernel_version
                    if node.status and node.status.node_info
                    else None
                ),
                "container_runtime_version": (
                    node.status.node_info.container_runtime_version
                    if node.status and node.status.node_info
                    else None
                ),
                "kubelet_version": (
                    node.status.node_info.kubelet_version
                    if node.status and node.status.node_info
                    else None
                ),
                "provider_id": node.spec.provider_id if node.spec else None,
                "ready": ready,
            }
        )
    return transformed_nodes


def load_nodes(
    session: neo4j.Session,
    nodes: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    logger.info(f"Loading {len(nodes)} kubernetes nodes.")
    load(
        session,
        KubernetesNodeSchema(),
        nodes,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


def cleanup(session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    logger.debug("Running cleanup job for KubernetesNode")
    GraphJob.from_node_schema(KubernetesNodeSchema(), common_job_parameters).run(
        session
    )


@timeit
def sync_nodes(
    session: neo4j.Session,
    client: K8sClient,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    nodes = get_nodes(client)
    transformed_nodes = transform_nodes(nodes)
    cluster_id: str = common_job_parameters["CLUSTER_ID"]
    load_nodes(session, transformed_nodes, update_tag, cluster_id, client.name)
    cleanup(session, common_job_parameters)
