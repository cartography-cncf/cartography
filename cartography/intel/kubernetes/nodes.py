import json
import logging
import re
from typing import Any

import neo4j
from kubernetes.client.exceptions import ApiException
from kubernetes.client.models import V1CSINode
from kubernetes.client.models import V1Node

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.container_arch import normalize_architecture
from cartography.intel.gcp.gke_utils import instance_id_from_provider_id
from cartography.intel.kubernetes.util import format_resource_quantities
from cartography.intel.kubernetes.util import get_gke_cluster_ref
from cartography.intel.kubernetes.util import get_gpu_quantity
from cartography.intel.kubernetes.util import k8s_paginate
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.nodes import KubernetesNodeSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_nodes(client: K8sClient) -> list[V1Node]:
    return k8s_paginate(client.core.list_node, raise_on_error=True)


@timeit
def get_csi_nodes(client: K8sClient) -> list[V1CSINode]:
    return k8s_paginate(client.storage.list_csi_node, raise_on_error=True)


def transform_csi_node_ids(csi_nodes: list[V1CSINode]) -> dict[str, dict[str, str]]:
    """Map each node name to the node ID every CSI driver registered for it.

    A ``CSINode`` object is named after its node. Each installed CSI driver
    records the ID it knows the node by (``spec.drivers[].nodeID``), which for
    cloud block-storage drivers is usually the cloud instance ID.
    """
    result: dict[str, dict[str, str]] = {}
    for csi_node in csi_nodes:
        drivers = getattr(csi_node.spec, "drivers", None) or []
        node_ids = {
            driver.name: driver.node_id
            for driver in drivers
            if driver.name and driver.node_id
        }
        if node_ids:
            result[csi_node.metadata.name] = node_ids
    return result


def _ec2_instance_id_from_provider_id(provider_id: str | None) -> str | None:
    """Extract the EC2 instance id from an EKS node's providerID.

    EKS sets ``spec.providerID`` to ``aws:///<availability-zone>/<instance-id>``.
    Other providers (GCE, Azure) use different formats and return None.
    """
    if not provider_id or not provider_id.startswith("aws://"):
        return None
    instance_id = provider_id.rsplit("/", 1)[-1]
    return instance_id if instance_id.startswith("i-") else None


# AKS sets `spec.providerID` to
# `azure:///subscriptions/<sub>/resourceGroups/<node resource group>/providers/...`.
_AZURE_PROVIDER_ID = re.compile(
    r"^azure:///subscriptions/([^/]+)/resourceGroups/([^/]+)/", re.IGNORECASE
)


def _azure_scope_from_provider_id(
    provider_id: str | None,
) -> tuple[str | None, str | None]:
    match = _AZURE_PROVIDER_ID.match(provider_id or "")
    if not match:
        return None, None
    return match.group(1).lower(), match.group(2).lower()


_SCALEWAY_INSTANCE_PROVIDER_ID_PREFIX = "scaleway://instance/"
_SCALEWAY_CSI_DRIVER = "csi.scaleway.com"
_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


def _scaleway_instance_id(
    provider_id: str | None,
    csi_node_ids: dict[str, str] | None,
) -> str | None:
    """Resolve the Scaleway Instance server ID backing a node.

    Kapsule and clusters running the Scaleway cloud controller manager set
    ``spec.providerID`` to ``scaleway://instance/<zone>/<server-id>``.
    Self-managed distributions without a cloud controller (k3s, kubeadm, ...)
    leave no Scaleway reference there, but the Scaleway CSI driver still
    registers each node as ``<zone>/<server-id>``, so fall back to that.
    """
    candidates: list[str | None] = []
    if provider_id and provider_id.startswith(_SCALEWAY_INSTANCE_PROVIDER_ID_PREFIX):
        candidates.append(provider_id)
    candidates.append((csi_node_ids or {}).get(_SCALEWAY_CSI_DRIVER))
    for candidate in candidates:
        server_id = (candidate or "").rsplit("/", 1)[-1]
        if _UUID.match(server_id):
            return server_id.lower()
    return None


def transform_nodes(
    nodes: list[V1Node],
    cluster_name: str,
    gke_resource_name: str | None = None,
    csi_node_ids: dict[str, dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    csi_node_ids = csi_node_ids or {}
    transformed = []
    for node in nodes:
        ni = node.status.node_info if node.status else None
        provider_id = getattr(getattr(node, "spec", None), "provider_id", None)
        labels = node.metadata.labels or {}
        capacity = node.status.capacity if node.status else None
        allocatable = node.status.allocatable if node.status else None
        gke_node_pool = labels.get("cloud.google.com/gke-nodepool")
        azure_subscription_id, azure_resource_group = _azure_scope_from_provider_id(
            provider_id
        )
        node_csi_ids = csi_node_ids.get(node.metadata.name)
        transformed.append(
            {
                "id": f"{cluster_name}/{node.metadata.name}",
                "name": node.metadata.name,
                "provider_id": provider_id,
                "instance_id": _ec2_instance_id_from_provider_id(provider_id),
                "gcp_instance_id": instance_id_from_provider_id(provider_id),
                "azure_subscription_id": azure_subscription_id,
                "azure_resource_group": azure_resource_group,
                "csi_node_ids": (
                    json.dumps(node_csi_ids, sort_keys=True) if node_csi_ids else None
                ),
                "scaleway_instance_id": _scaleway_instance_id(
                    provider_id, node_csi_ids
                ),
                "gke_node_pool": gke_node_pool,
                "gke_node_pool_id": (
                    f"{gke_resource_name}/nodePools/{gke_node_pool}"
                    if gke_resource_name and gke_node_pool
                    else None
                ),
                "labels": json.dumps(labels, sort_keys=True),
                "capacity": format_resource_quantities(capacity),
                "allocatable": format_resource_quantities(allocatable),
                "gpu_capacity": get_gpu_quantity(capacity),
                "gpu_allocatable": get_gpu_quantity(allocatable),
                "gpu_product": labels.get("nvidia.com/gpu.product")
                or labels.get("cloud.google.com/gke-accelerator"),
                "architecture": getattr(ni, "architecture", None),
                "architecture_normalized": normalize_architecture(
                    getattr(ni, "architecture", None),
                ),
                "os": getattr(ni, "operating_system", None),
                "os_image": getattr(ni, "os_image", None),
                "kernel_version": getattr(ni, "kernel_version", None),
                "container_runtime_version": getattr(
                    ni,
                    "container_runtime_version",
                    None,
                ),
                "kubelet_version": getattr(ni, "kubelet_version", None),
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
) -> dict[str, str]:
    try:
        raw_nodes = get_nodes(client)
    except ApiException as err:
        if err.status in (401, 403):
            # A partial nodes snapshot cannot be told apart from an empty one, so skip
            # load + cleanup and keep the previous data, like `sync_secrets`.
            logger.warning(
                "Cartography lacks permission to list nodes on cluster %s (status %s). "
                "Skipping nodes sync and preserving previously synced data.",
                client.name,
                err.status,
            )
            return {}
        raise
    try:
        csi_node_ids = transform_csi_node_ids(get_csi_nodes(client))
    except ApiException as err:
        if err.status not in (401, 403):
            raise
        # CSINode data only enriches nodes with the IDs their CSI drivers know
        # them by, so nodes still sync without it.
        logger.warning(
            "Cartography lacks permission to list csinodes on cluster %s (status %s). "
            "Nodes are synced without CSI driver node IDs, so nodes that only "
            "expose their cloud instance through a CSI driver are not linked to it.",
            client.name,
            err.status,
        )
        csi_node_ids = {}
    gke_ref = get_gke_cluster_ref(client)
    transformed = transform_nodes(
        raw_nodes,
        client.name,
        gke_ref.resource_name if gke_ref else None,
        csi_node_ids,
    )
    load_nodes(
        session,
        transformed,
        update_tag,
        common_job_parameters["CLUSTER_ID"],
        client.name,
    )
    cleanup(session, common_job_parameters)
    # Return a node-name → architecture_normalized lookup so callers can stamp
    # the runtime arch onto pods and containers without a graph traversal.
    return {
        n["name"]: n["architecture_normalized"]
        for n in transformed
        if n.get("architecture_normalized")
    }
