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
class KubernetesPodNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    status_phase: PropertyRef = PropertyRef("status_phase")
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    deletion_timestamp: PropertyRef = PropertyRef("deletion_timestamp")
    namespace: PropertyRef = PropertyRef("namespace", extra_index=True)
    labels: PropertyRef = PropertyRef("labels")
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME", set_in_kwargs=True, extra_index=True
    )
    node: PropertyRef = PropertyRef("node")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesPodToKubernetesNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesPod)<-[:CONTAINS]-(:KubernetesNamespace)
class KubernetesPodToKubernetesNamespaceRel(CartographyRelSchema):
    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesPodToKubernetesNamespaceRelProperties = (
        KubernetesPodToKubernetesNamespaceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesPodToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesPod)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesPodToKubernetesClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesPodToKubernetesClusterRelProperties = (
        KubernetesPodToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesPodSchema(CartographyNodeSchema):
    label: str = "KubernetesPod"
    properties: KubernetesPodNodeProperties = KubernetesPodNodeProperties()
    sub_resource_relationship: KubernetesPodToKubernetesClusterRel = (
        KubernetesPodToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [KubernetesPodToKubernetesNamespaceRel()]
    )
