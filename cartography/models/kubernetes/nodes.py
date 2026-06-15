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
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME", set_in_kwargs=True, extra_index=True
    )
    architecture: PropertyRef = PropertyRef("architecture")
    architecture_normalized: PropertyRef = PropertyRef("architecture_normalized")
    os: PropertyRef = PropertyRef("os")
    os_image: PropertyRef = PropertyRef("os_image")
    kernel_version: PropertyRef = PropertyRef("kernel_version")
    container_runtime_version: PropertyRef = PropertyRef("container_runtime_version")
    kubelet_version: PropertyRef = PropertyRef("kubelet_version")
    # Cloud provider instance reference (e.g. EKS: aws:///<az>/<instance-id>)
    provider_id: PropertyRef = PropertyRef("provider_id")
    instance_id: PropertyRef = PropertyRef("instance_id", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesNodeToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesNode)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesNodeToKubernetesClusterRel(CartographyRelSchema):
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
