from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class KubernetesNodeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    deletion_timestamp: PropertyRef = PropertyRef("deletion_timestamp")
    architecture: PropertyRef = PropertyRef("architecture")
    operating_system: PropertyRef = PropertyRef("operating_system")
    os_image: PropertyRef = PropertyRef("os_image")
    kernel_version: PropertyRef = PropertyRef("kernel_version")
    container_runtime_version: PropertyRef = PropertyRef("container_runtime_version")
    kubelet_version: PropertyRef = PropertyRef("kubelet_version")
    provider_id: PropertyRef = PropertyRef("provider_id")
    ready: PropertyRef = PropertyRef("ready")
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME", set_in_kwargs=True, extra_index=True
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesNodeToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesNode)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesNodeToKubernetesClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesNodeToKubernetesClusterRelProperties = (
        KubernetesNodeToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesNodeSchema(CartographyNodeSchema):
    label: str = "KubernetesNode"
    properties: KubernetesNodeNodeProperties = KubernetesNodeNodeProperties()
    sub_resource_relationship: KubernetesNodeToKubernetesClusterRel = (
        KubernetesNodeToKubernetesClusterRel()
    )
