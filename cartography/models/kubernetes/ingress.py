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
class KubernetesIngressNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    name: PropertyRef = PropertyRef("name")
    namespace: PropertyRef = PropertyRef("namespace", extra_index=True)
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    deletion_timestamp: PropertyRef = PropertyRef("deletion_timestamp")
    ingress_class_name: PropertyRef = PropertyRef("ingress_class_name")
    rules: PropertyRef = PropertyRef("rules")
    annotations: PropertyRef = PropertyRef("annotations")
    default_backend: PropertyRef = PropertyRef("default_backend")
    cluster_name: PropertyRef = PropertyRef("CLUSTER_NAME", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesIngressToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesIngress)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesIngressToKubernetesClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesIngressToKubernetesClusterRelProperties = (
        KubernetesIngressToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesIngressToKubernetesNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesIngress)<-[:CONTAINS]-(:KubernetesNamespace)
class KubernetesIngressToKubernetesNamespaceRel(CartographyRelSchema):
    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesIngressToKubernetesNamespaceRelProperties = (
        KubernetesIngressToKubernetesNamespaceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesIngressToKubernetesServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesIngress)-[:TARGETS]->(:KubernetesService)
class KubernetesIngressToKubernetesServiceRel(CartographyRelSchema):
    target_node_label: str = "KubernetesService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "namespace": PropertyRef("namespace"),
            "name": PropertyRef("target_services", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TARGETS"
    properties: KubernetesIngressToKubernetesServiceRelProperties = (
        KubernetesIngressToKubernetesServiceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesIngressSchema(CartographyNodeSchema):
    label: str = "KubernetesIngress"
    properties: KubernetesIngressNodeProperties = KubernetesIngressNodeProperties()
    sub_resource_relationship: KubernetesIngressToKubernetesClusterRel = (
        KubernetesIngressToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesIngressToKubernetesNamespaceRel(),
            KubernetesIngressToKubernetesServiceRel(),
        ]
    )
