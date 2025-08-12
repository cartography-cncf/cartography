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
class KubernetesServiceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    deletion_timestamp: PropertyRef = PropertyRef("deletion_timestamp")
    namespace: PropertyRef = PropertyRef("namespace", extra_index=True)
    selector: PropertyRef = PropertyRef("selector")
    type: PropertyRef = PropertyRef("type")
    cluster_ip: PropertyRef = PropertyRef("cluster_ip")
    load_balancer_ip: PropertyRef = PropertyRef("load_balancer_ip")
    load_balancer_ingress: PropertyRef = PropertyRef("load_balancer_ingress")
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME", set_in_kwargs=True, extra_index=True
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesServiceToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesService)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesServiceToKubernetesClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesServiceToKubernetesClusterRelProperties = (
        KubernetesServiceToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesServiceToKubernetesNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesService)<-[:CONTAINS]-(:KubernetesNamespace)
class KubernetesServiceToKubernetesNamespaceRel(CartographyRelSchema):
    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesServiceToKubernetesNamespaceRelProperties = (
        KubernetesServiceToKubernetesNamespaceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesServiceToKubernetesPodRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesService)-[:TARGET]->(:KubernetesPod)
class KubernetesServiceToKubernetesPodRel(CartographyRelSchema):
    target_node_label: str = "KubernetesPod"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "namespace": PropertyRef("namespace"),
            "id": PropertyRef("pod_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TARGETS"
    properties: KubernetesServiceToKubernetesPodRelProperties = (
        KubernetesServiceToKubernetesPodRelProperties()
    )


@dataclass(frozen=True)
class KubernetesServiceSchema(CartographyNodeSchema):
    label: str = "KubernetesService"
    properties: KubernetesServiceNodeProperties = KubernetesServiceNodeProperties()
    sub_resource_relationship: KubernetesServiceToKubernetesClusterRel = (
        KubernetesServiceToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesServiceToKubernetesNamespaceRel(),
            KubernetesServiceToKubernetesPodRel(),
        ]
    )
