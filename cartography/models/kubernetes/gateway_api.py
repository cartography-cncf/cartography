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
    id: PropertyRef = PropertyRef("uid", description="UID of the Gateway.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the Gateway."
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        extra_index=True,
        description="The Kubernetes namespace where this Gateway is deployed.",
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="`<namespace>/<name>` identifier used to match the Gateway from `HTTPRoute.spec.parentRefs`.",
    )
    gateway_class_name: PropertyRef = PropertyRef(
        "gateway_class_name",
        description="Name of the `GatewayClass` referenced by `spec.gatewayClassName`.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Epoch seconds of `metadata.creationTimestamp`.",
    )
    deletion_timestamp: PropertyRef = PropertyRef(
        "deletion_timestamp",
        description="Epoch seconds of `metadata.deletionTimestamp`.",
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster where this Gateway is deployed.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class KubernetesGatewayToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesGatewayToKubernetesClusterRel(CartographyRelSchema):
    "Links `KubernetesCluster` to `KubernetesGateway` with `RESOURCE`."

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
    "Links `KubernetesNamespace` to `KubernetesGateway` with `CONTAINS`."

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
    "Links `KubernetesGateway` to `KubernetesHTTPRoute` with `ROUTES`."

    target_node_label: str = "KubernetesHTTPRoute"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "qualified_name": PropertyRef(
                "attached_route_qualified_names", one_to_many=True
            ),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTES"
    properties: KubernetesGatewayToHTTPRouteRelProperties = (
        KubernetesGatewayToHTTPRouteRelProperties()
    )


@dataclass(frozen=True)
class KubernetesGatewaySchema(CartographyNodeSchema):
    "A Gateway API gateway that accepts traffic for attached routes."

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
    id: PropertyRef = PropertyRef("uid", description="UID of the HTTPRoute.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the HTTPRoute."
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        extra_index=True,
        description="The Kubernetes namespace where this HTTPRoute is deployed.",
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="`<namespace>/<name>` identifier used to match this HTTPRoute from `Gateway` parents.",
    )
    hostnames: PropertyRef = PropertyRef(
        "hostnames", description="List of hostnames from `spec.hostnames`."
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Epoch seconds of `metadata.creationTimestamp`.",
    )
    deletion_timestamp: PropertyRef = PropertyRef(
        "deletion_timestamp",
        description="Epoch seconds of `metadata.deletionTimestamp`.",
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster where this HTTPRoute is deployed.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class KubernetesHTTPRouteToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesHTTPRouteToKubernetesClusterRel(CartographyRelSchema):
    "Links `KubernetesCluster` to `KubernetesHTTPRoute` with `RESOURCE`."

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
    "Links `KubernetesNamespace` to `KubernetesHTTPRoute` with `CONTAINS`."

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
    "Links `KubernetesHTTPRoute` to `KubernetesService` with `TARGETS`."

    target_node_label: str = "KubernetesService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "qualified_name": PropertyRef(
                "backend_service_qualified_names", one_to_many=True
            ),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TARGETS"
    properties: KubernetesHTTPRouteToKubernetesServiceRelProperties = (
        KubernetesHTTPRouteToKubernetesServiceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesHTTPRouteSchema(CartographyNodeSchema):
    "A Gateway API HTTPRoute that forwards traffic to services."

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
