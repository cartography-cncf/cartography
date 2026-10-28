from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class KubernetesNodeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Identifier for the node derived from cluster name and node name (e.g. `my-cluster/my-node`).",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the Kubernetes node."
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster this node belongs to.",
    )
    architecture: PropertyRef = PropertyRef(
        "architecture",
        description="Raw CPU architecture as reported by the node (e.g. `amd64`, `arm64`).",
    )
    architecture_normalized: PropertyRef = PropertyRef(
        "architecture_normalized",
        description="Canonical CPU architecture after normalization (e.g. `x86_64` → `amd64`, `aarch64` → `arm64`).",
    )
    os: PropertyRef = PropertyRef(
        "os", description="Operating system of the node (e.g. `linux`)."
    )
    os_image: PropertyRef = PropertyRef(
        "os_image",
        description="Human-readable OS image name (e.g. `Ubuntu 22.04.3 LTS`).",
    )
    kernel_version: PropertyRef = PropertyRef(
        "kernel_version",
        description="Kernel version of the node (e.g. `5.15.0-1034-aws`).",
    )
    container_runtime_version: PropertyRef = PropertyRef(
        "container_runtime_version",
        description="Container runtime and version (e.g. `containerd://1.7.0`).",
    )
    kubelet_version: PropertyRef = PropertyRef(
        "kubelet_version",
        description="Version of the kubelet running on the node (e.g. `v1.27.1`).",
    )
    # Cloud provider instance reference (e.g. EKS: aws:///<az>/<instance-id>)
    provider_id: PropertyRef = PropertyRef(
        "provider_id",
        description="Cloud provider instance reference from the node's `spec.providerID` (e.g. EKS: `aws:///us-east-1a/i-0123456789abcdef0`).",
    )
    instance_id: PropertyRef = PropertyRef(
        "instance_id",
        extra_index=True,
        description="EC2 instance id parsed from `provider_id` for EKS nodes (e.g. `i-0123456789abcdef0`); null for non-AWS providers.",
    )
    gcp_instance_id: PropertyRef = PropertyRef(
        "gcp_instance_id",
        description="Compute Engine instance partial URI (`projects/{project}/zones/{zone}/instances/{name}`) parsed from the Kubernetes `Node.spec.providerID` (`gce://{project}/{zone}/{name}`); null for non-GCE providers.",
    )
    azure_subscription_id: PropertyRef = PropertyRef(
        "azure_subscription_id",
        description="Lowercased Azure subscription ID parsed from an AKS node's `provider_id` (`azure:///subscriptions/{subscription}/resourceGroups/{resource group}/...`); null for non-Azure providers. Scopes matching of AKS load balancers.",
    )
    azure_resource_group: PropertyRef = PropertyRef(
        "azure_resource_group",
        description="Lowercased node resource group parsed from an AKS node's `provider_id`; null for non-Azure providers. AKS creates the cluster's Azure load balancers in this resource group.",
    )
    gke_node_pool: PropertyRef = PropertyRef(
        "gke_node_pool",
        description='GKE node pool name from the Kubernetes `Node.metadata.labels["cloud.google.com/gke-nodepool"]` label; null for non-GKE nodes.',
    )
    labels: PropertyRef = PropertyRef(
        "labels",
        description="Node metadata labels stored as a JSON-encoded object.",
    )
    capacity: PropertyRef = PropertyRef(
        "capacity",
        description="Node resource capacity from `status.capacity`, stored as a JSON-encoded object.",
    )
    allocatable: PropertyRef = PropertyRef(
        "allocatable",
        description="Node allocatable resources from `status.allocatable`, stored as a JSON-encoded object.",
    )
    gpu_capacity: PropertyRef = PropertyRef(
        "gpu_capacity",
        description="Total GPU scheduling-unit capacity across full-GPU, NVIDIA MIG, and Intel GPU resource keys; heterogeneous units are not normalized to physical GPUs.",
    )
    gpu_allocatable: PropertyRef = PropertyRef(
        "gpu_allocatable",
        description="Total allocatable GPU scheduling units across full-GPU, NVIDIA MIG, and Intel GPU resource keys; heterogeneous units are not normalized to physical GPUs.",
    )
    gpu_product: PropertyRef = PropertyRef(
        "gpu_product",
        extra_index=True,
        description="GPU product reported by the standard NVIDIA GPU Feature Discovery or GKE accelerator label.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesNodeToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesNode)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesNodeToKubernetesClusterRel(CartographyRelSchema):
    """Links a cluster to one of its nodes."""

    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesNodeToKubernetesClusterRelProperties = (
        KubernetesNodeToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesNodeToEC2InstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesNode)-[:IS_INSTANCE]->(:AWSEC2Instance)
# Only created for EKS nodes whose providerID resolves to an EC2 instance id.
class KubernetesNodeToEC2InstanceRel(CartographyRelSchema):
    """Links a node to the EC2 instance backing it."""

    target_node_label: str = "AWSEC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("instance_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IS_INSTANCE"
    properties: KubernetesNodeToEC2InstanceRelProperties = (
        KubernetesNodeToEC2InstanceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesNodeToGCPInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesNode)-[:IS_INSTANCE]->(:GCPInstance)
# Only created for GKE nodes whose providerID resolves to a Compute Engine instance.
class KubernetesNodeToGCPInstanceRel(CartographyRelSchema):
    """Links a node to the Compute Engine instance backing it. Autopilot VMs are not visible to the Compute API, so this edge is absent for Autopilot clusters."""

    target_node_label: str = "GCPInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("gcp_instance_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IS_INSTANCE"
    properties: KubernetesNodeToGCPInstanceRelProperties = (
        KubernetesNodeToGCPInstanceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesNodeToGKENodePoolRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesNode)-[:MEMBER_OF]->(:GKENodePool)
# Only created for clusters ingested with GKE metadata (`--gke-cluster` or `--managed-kubernetes gke`).
class KubernetesNodeToGKENodePoolRel(CartographyRelSchema):
    """Links a node to the GKE node pool named by its `cloud.google.com/gke-nodepool` label."""

    target_node_label: str = "GKENodePool"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("gke_node_pool_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: KubernetesNodeToGKENodePoolRelProperties = (
        KubernetesNodeToGKENodePoolRelProperties()
    )


@dataclass(frozen=True)
class KubernetesNodeSchema(CartographyNodeSchema):
    "A worker node registered with a Kubernetes cluster."

    label: str = "KubernetesNode"
    properties: KubernetesNodeNodeProperties = KubernetesNodeNodeProperties()
    sub_resource_relationship: KubernetesNodeToKubernetesClusterRel = (
        KubernetesNodeToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesNodeToEC2InstanceRel(),
            KubernetesNodeToGCPInstanceRel(),
            KubernetesNodeToGKENodePoolRel(),
        ]
    )
