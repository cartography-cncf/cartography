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
    id: PropertyRef = PropertyRef("id", description="Load Balancer unique ID.")
    name: PropertyRef = PropertyRef("name", description="Load Balancer name.")
    description: PropertyRef = PropertyRef(
        "description", description="Load Balancer description."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Load Balancer status (e.g. `ready`)."
    )
    type: PropertyRef = PropertyRef(
        "type_", description="Load Balancer commercial type (e.g. `LB-S`)."
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags associated with the Load Balancer."
    )
    frontend_count: PropertyRef = PropertyRef(
        "frontend_count", description="Number of frontends."
    )
    backend_count: PropertyRef = PropertyRef(
        "backend_count", description="Number of backends."
    )
    private_network_count: PropertyRef = PropertyRef(
        "private_network_count", description="Number of attached Private Networks."
    )
    route_count: PropertyRef = PropertyRef(
        "route_count", description="Number of routes."
    )
    ssl_compatibility_level: PropertyRef = PropertyRef(
        "ssl_compatibility_level", description="SSL compatibility level."
    )
    # Public entry-point IP(s) of the load balancer.
    ip_address: PropertyRef = PropertyRef(
        "ip_address",
        description="Primary public IP address (first entry of `ip_addresses`).",
    )
    ip_addresses: PropertyRef = PropertyRef(
        "ip_addresses", description="All public IP addresses of the Load Balancer."
    )
    zone: PropertyRef = PropertyRef(
        "zone", description="Zone the Load Balancer lives in."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Region the Load Balancer lives in."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Load Balancer creation date."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Load Balancer last update date."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayLoadBalancerToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayLoadBalancer)
class ScalewayLoadBalancerToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayLoadBalancer` through `RESOURCE`."""

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
    """A Load Balancer distributes incoming traffic across backend servers. Its public
    IP(s) make it an internet-facing entry point.
    """

    label: str = "ScalewayLoadBalancer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["LoadBalancer"])
    properties: ScalewayLoadBalancerProperties = ScalewayLoadBalancerProperties()
    sub_resource_relationship: ScalewayLoadBalancerToProjectRel = (
        ScalewayLoadBalancerToProjectRel()
    )


@dataclass(frozen=True)
class ScalewayLBFrontendProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Frontend unique ID.")
    name: PropertyRef = PropertyRef("name", description="Frontend name.")
    inbound_port: PropertyRef = PropertyRef(
        "inbound_port", description="Port the frontend listens on."
    )
    certificate_ids: PropertyRef = PropertyRef(
        "certificate_ids", description="IDs of the TLS certificates attached."
    )
    enable_http3: PropertyRef = PropertyRef(
        "enable_http3", description="True if HTTP/3 is enabled."
    )
    enable_access_logs: PropertyRef = PropertyRef(
        "enable_access_logs", description="True if access logs are enabled."
    )
    timeout_client: PropertyRef = PropertyRef(
        "timeout_client", description="Client inactivity timeout."
    )
    connection_rate_limit: PropertyRef = PropertyRef(
        "connection_rate_limit", description="Per-source connection rate limit."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Frontend creation date."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Frontend last update date."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayLBFrontendToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayLBFrontend)
class ScalewayLBFrontendToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayLBFrontend` through `RESOURCE`."""

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
    """Connects `ScalewayLoadBalancer` to `ScalewayLBFrontend` through `HAS`."""

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
    """Connects `ScalewayLBFrontend` to `ScalewayLBBackend` through `ROUTES_TO`."""

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
    """A Frontend defines an inbound listener (port) on a Load Balancer and the backend it
    routes to.
    """

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
    id: PropertyRef = PropertyRef("id", description="Backend unique ID.")
    name: PropertyRef = PropertyRef("name", description="Backend name.")
    forward_protocol: PropertyRef = PropertyRef(
        "forward_protocol",
        description="Protocol used to forward traffic (`tcp`, `http`).",
    )
    forward_port: PropertyRef = PropertyRef(
        "forward_port", description="Port traffic is forwarded to."
    )
    forward_port_algorithm: PropertyRef = PropertyRef(
        "forward_port_algorithm",
        description="Load-balancing algorithm (e.g. `roundrobin`).",
    )
    sticky_sessions: PropertyRef = PropertyRef(
        "sticky_sessions", description="Sticky-session mode."
    )
    on_marked_down_action: PropertyRef = PropertyRef(
        "on_marked_down_action", description="Action when a server is marked down."
    )
    proxy_protocol: PropertyRef = PropertyRef(
        "proxy_protocol", description="Proxy protocol mode."
    )
    # Backend server pool (list of server IP addresses).
    pool: PropertyRef = PropertyRef(
        "pool", description="List of backend server IP addresses."
    )
    health_check_port: PropertyRef = PropertyRef(
        "health_check.port", description="Port used for health checks."
    )
    health_check_delay: PropertyRef = PropertyRef(
        "health_check.check_delay", description="Delay between health checks."
    )
    health_check_max_retries: PropertyRef = PropertyRef(
        "health_check.check_max_retries",
        description="Max health-check retries before marking down.",
    )
    timeout_server: PropertyRef = PropertyRef(
        "timeout_server", description="Server inactivity timeout."
    )
    timeout_connect: PropertyRef = PropertyRef(
        "timeout_connect", description="Connection timeout."
    )
    ssl_bridging: PropertyRef = PropertyRef(
        "ssl_bridging", description="True if SSL bridging to the backend is enabled."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Backend creation date."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Backend last update date."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayLBBackendToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayLBBackend)
class ScalewayLBBackendToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayLBBackend` through `RESOURCE`."""

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
    """Connects `ScalewayLoadBalancer` to `ScalewayLBBackend` through `HAS`."""

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
    """A Backend defines a pool of servers and the forwarding / health-check configuration
    a Load Balancer uses to reach them.
    """

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
