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
class KubernetesNamespaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    deletion_timestamp: PropertyRef = PropertyRef("deletion_timestamp")
    status_phase: PropertyRef = PropertyRef("status_phase")
    cluster_name: PropertyRef = PropertyRef(
        "cluster_name", set_in_kwargs=True, extra_index=True
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesNamespaceToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesNamespace)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesNamespaceToKubernetesClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesNamespaceToKubernetesClusterRelProperties = (
        KubernetesNamespaceToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesNamespaceSchema(CartographyNodeSchema):
    label: str = "KubernetesNamespace"
    properties: KubernetesNamespaceNodeProperties = KubernetesNamespaceNodeProperties()
    sub_resource_relationship: KubernetesNamespaceToKubernetesClusterRel = (
        KubernetesNamespaceToKubernetesClusterRel()
    )
