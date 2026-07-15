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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class KubernetesNodeToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesNode)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesNodeToKubernetesClusterRel(CartographyRelSchema):
    "Links `KubernetesCluster` to `KubernetesNode` with `RESOURCE`."

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
# (:KubernetesNode)-[:IS_INSTANCE]->(:EC2Instance)
# Only created for EKS nodes whose providerID resolves to an EC2 instance id.
class KubernetesNodeToEC2InstanceRel(CartographyRelSchema):
    "Links `KubernetesNode` to `EC2Instance` with `IS_INSTANCE`."

    target_node_label: str = "EC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("instance_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IS_INSTANCE"
    properties: KubernetesNodeToEC2InstanceRelProperties = (
        KubernetesNodeToEC2InstanceRelProperties()
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
        ]
    )
