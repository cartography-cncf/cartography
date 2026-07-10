from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ScalewayLoadBalancerProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    status: PropertyRef = PropertyRef("status")
    type: PropertyRef = PropertyRef("type_")
    tags: PropertyRef = PropertyRef("tags")
    frontend_count: PropertyRef = PropertyRef("frontend_count")
    backend_count: PropertyRef = PropertyRef("backend_count")
    private_network_count: PropertyRef = PropertyRef("private_network_count")
    route_count: PropertyRef = PropertyRef("route_count")
    ssl_compatibility_level: PropertyRef = PropertyRef("ssl_compatibility_level")
    # Public entry-point IP(s) of the load balancer.
    ip_address: PropertyRef = PropertyRef("ip_address")
    ip_addresses: PropertyRef = PropertyRef("ip_addresses")
    zone: PropertyRef = PropertyRef("zone")
    region: PropertyRef = PropertyRef("region")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayLoadBalancerToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayLoadBalancer)
class ScalewayLoadBalancerToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayLoadBalancerToProjectRelProperties = (
        ScalewayLoadBalancerToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayLoadBalancerSchema(CartographyNodeSchema):
    label: str = "ScalewayLoadBalancer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["LoadBalancer"])
    properties: ScalewayLoadBalancerProperties = ScalewayLoadBalancerProperties()
    sub_resource_relationship: ScalewayLoadBalancerToProjectRel = (
        ScalewayLoadBalancerToProjectRel()
    )


@dataclass(frozen=True)
class ScalewayLBFrontendProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    inbound_port: PropertyRef = PropertyRef("inbound_port")
    certificate_ids: PropertyRef = PropertyRef("certificate_ids")
    enable_http3: PropertyRef = PropertyRef("enable_http3")
    enable_access_logs: PropertyRef = PropertyRef("enable_access_logs")
    timeout_client: PropertyRef = PropertyRef("timeout_client")
    connection_rate_limit: PropertyRef = PropertyRef("connection_rate_limit")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayLBFrontendToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayLBFrontend)
class ScalewayLBFrontendToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayLBFrontendToProjectRelProperties = (
        ScalewayLBFrontendToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayLBFrontendToLBRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayLoadBalancer)-[:HAS]->(:ScalewayLBFrontend)
class ScalewayLBFrontendToLBRel(CartographyRelSchema):
    target_node_label: str = "ScalewayLoadBalancer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("lb_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayLBFrontendToLBRelProperties = (
        ScalewayLBFrontendToLBRelProperties()
    )


@dataclass(frozen=True)
class ScalewayLBFrontendToBackendRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayLBFrontend)-[:ROUTES_TO]->(:ScalewayLBBackend)
class ScalewayLBFrontendToBackendRel(CartographyRelSchema):
    target_node_label: str = "ScalewayLBBackend"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("backend_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTES_TO"
    properties: ScalewayLBFrontendToBackendRelProperties = (
        ScalewayLBFrontendToBackendRelProperties()
    )


@dataclass(frozen=True)
class ScalewayLBFrontendSchema(CartographyNodeSchema):
    label: str = "ScalewayLBFrontend"
    properties: ScalewayLBFrontendProperties = ScalewayLBFrontendProperties()
    sub_resource_relationship: ScalewayLBFrontendToProjectRel = (
        ScalewayLBFrontendToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayLBFrontendToLBRel(),
            ScalewayLBFrontendToBackendRel(),
        ]
    )


@dataclass(frozen=True)
class ScalewayLBBackendProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    forward_protocol: PropertyRef = PropertyRef("forward_protocol")
    forward_port: PropertyRef = PropertyRef("forward_port")
    forward_port_algorithm: PropertyRef = PropertyRef("forward_port_algorithm")
    sticky_sessions: PropertyRef = PropertyRef("sticky_sessions")
    on_marked_down_action: PropertyRef = PropertyRef("on_marked_down_action")
    proxy_protocol: PropertyRef = PropertyRef("proxy_protocol")
    # Backend server pool (list of server IP addresses).
    pool: PropertyRef = PropertyRef("pool")
    health_check_port: PropertyRef = PropertyRef("health_check.port")
    health_check_delay: PropertyRef = PropertyRef("health_check.check_delay")
    health_check_max_retries: PropertyRef = PropertyRef(
        "health_check.check_max_retries"
    )
    timeout_server: PropertyRef = PropertyRef("timeout_server")
    timeout_connect: PropertyRef = PropertyRef("timeout_connect")
    ssl_bridging: PropertyRef = PropertyRef("ssl_bridging")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayLBBackendToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayLBBackend)
class ScalewayLBBackendToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayLBBackendToProjectRelProperties = (
        ScalewayLBBackendToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayLBBackendToLBRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayLoadBalancer)-[:HAS]->(:ScalewayLBBackend)
class ScalewayLBBackendToLBRel(CartographyRelSchema):
    target_node_label: str = "ScalewayLoadBalancer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("lb_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayLBBackendToLBRelProperties = (
        ScalewayLBBackendToLBRelProperties()
    )


@dataclass(frozen=True)
class ScalewayLBBackendSchema(CartographyNodeSchema):
    label: str = "ScalewayLBBackend"
    properties: ScalewayLBBackendProperties = ScalewayLBBackendProperties()
    sub_resource_relationship: ScalewayLBBackendToProjectRel = (
        ScalewayLBBackendToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayLBBackendToLBRel(),
        ]
    )
