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
class KubernetesGatewayNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    namespace: PropertyRef = PropertyRef("namespace", extra_index=True)
    gateway_class_name: PropertyRef = PropertyRef("gateway_class_name")
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    deletion_timestamp: PropertyRef = PropertyRef("deletion_timestamp")
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME", set_in_kwargs=True, extra_index=True
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesGatewayToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesGatewayToKubernetesClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesGatewayToKubernetesClusterRelProperties = (
        KubernetesGatewayToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesGatewayToKubernetesNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesGatewayToKubernetesNamespaceRel(CartographyRelSchema):
    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesGatewayToKubernetesNamespaceRelProperties = (
        KubernetesGatewayToKubernetesNamespaceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesGatewayToHTTPRouteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesGatewayToHTTPRouteRel(CartographyRelSchema):
    target_node_label: str = "KubernetesHTTPRoute"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "namespace": PropertyRef("attached_route_namespaces", one_to_many=True),
            "name": PropertyRef("attached_route_names", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTES"
    properties: KubernetesGatewayToHTTPRouteRelProperties = (
        KubernetesGatewayToHTTPRouteRelProperties()
    )


@dataclass(frozen=True)
class KubernetesGatewaySchema(CartographyNodeSchema):
    label: str = "KubernetesGateway"
    properties: KubernetesGatewayNodeProperties = KubernetesGatewayNodeProperties()
    sub_resource_relationship: KubernetesGatewayToKubernetesClusterRel = (
        KubernetesGatewayToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesGatewayToKubernetesNamespaceRel(),
            KubernetesGatewayToHTTPRouteRel(),
        ]
    )


@dataclass(frozen=True)
class KubernetesHTTPRouteNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    namespace: PropertyRef = PropertyRef("namespace", extra_index=True)
    hostnames: PropertyRef = PropertyRef("hostnames")
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    deletion_timestamp: PropertyRef = PropertyRef("deletion_timestamp")
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME", set_in_kwargs=True, extra_index=True
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesHTTPRouteToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesHTTPRouteToKubernetesClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesHTTPRouteToKubernetesClusterRelProperties = (
        KubernetesHTTPRouteToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesHTTPRouteToKubernetesNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesHTTPRouteToKubernetesNamespaceRel(CartographyRelSchema):
    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesHTTPRouteToKubernetesNamespaceRelProperties = (
        KubernetesHTTPRouteToKubernetesNamespaceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesHTTPRouteToKubernetesServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesHTTPRouteToKubernetesServiceRel(CartographyRelSchema):
    target_node_label: str = "KubernetesService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "namespace": PropertyRef("backend_service_namespaces", one_to_many=True),
            "name": PropertyRef("backend_service_names", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TARGETS"
    properties: KubernetesHTTPRouteToKubernetesServiceRelProperties = (
        KubernetesHTTPRouteToKubernetesServiceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesHTTPRouteSchema(CartographyNodeSchema):
    label: str = "KubernetesHTTPRoute"
    properties: KubernetesHTTPRouteNodeProperties = KubernetesHTTPRouteNodeProperties()
    sub_resource_relationship: KubernetesHTTPRouteToKubernetesClusterRel = (
        KubernetesHTTPRouteToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesHTTPRouteToKubernetesNamespaceRel(),
            KubernetesHTTPRouteToKubernetesServiceRel(),
        ]
    )
