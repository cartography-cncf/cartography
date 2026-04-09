import logging
from typing import Any

import neo4j
from kubernetes.client.models import V1Node

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import k8s_paginate
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.nodes import KubernetesNodeSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_ARCH_NORMALIZATION_MAP = {
    "amd64": "amd64",
    "x86_64": "amd64",
    "arm64": "arm64",
    "aarch64": "arm64",
}


def _normalize_architecture(arch: str | None) -> str | None:
    if arch is None:
        return None
    return _ARCH_NORMALIZATION_MAP.get(arch.lower(), arch.lower())


@timeit
def get_nodes(client: K8sClient) -> list[V1Node]:
    return k8s_paginate(client.core.list_node)


def transform_nodes(nodes: list[V1Node], cluster_name: str) -> list[dict[str, Any]]:
    transformed = []
    for node in nodes:
        node_info = node.status.node_info if node.status else None
        arch_raw = node_info.architecture if node_info else None
        transformed.append(
            {
                "id": f"{cluster_name}/{node.metadata.name}",
                "name": node.metadata.name,
                "architecture": arch_raw,
                "architecture_normalized": _normalize_architecture(arch_raw),
                "os": node_info.operating_system if node_info else None,
                "os_image": node_info.os_image if node_info else None,
                "kernel_version": node_info.kernel_version if node_info else None,
                "container_runtime_version": (
                    node_info.container_runtime_version if node_info else None
                ),
                "kubelet_version": node_info.kubelet_version if node_info else None,
            }
        )
    return transformed


def load_nodes(
    session: neo4j.Session,
    nodes: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
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
    raw_nodes = get_nodes(client)
    transformed = transform_nodes(raw_nodes, client.name)
    load_nodes(
        session,
        transformed,
        update_tag,
        common_job_parameters["CLUSTER_ID"],
        client.name,
    )
    cleanup(session, common_job_parameters)
