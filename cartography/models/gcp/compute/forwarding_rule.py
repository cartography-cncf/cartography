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
class GCPForwardingRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "partial_uri",
        description="A partial resource URI representing this Forwarding Rule.",
    )
    partial_uri: PropertyRef = PropertyRef("partial_uri", description="Same as `id`.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    ip_address: PropertyRef = PropertyRef(
        "ip_address", description="IP address that this Forwarding Rule serves."
    )
    ip_protocol: PropertyRef = PropertyRef(
        "ip_protocol", description="IP protocol to which this rule applies."
    )
    load_balancing_scheme: PropertyRef = PropertyRef(
        "load_balancing_scheme", description="Specifies the Forwarding Rule type."
    )
    lb_type: PropertyRef = PropertyRef(
        "lb_type",
        description="Normalised load-balancer family derived from the target proxy collection (`http`, `https`, `tcp`, `ssl`, `grpc`, `network`, `vpn`).",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the Forwarding Rule."
    )
    network: PropertyRef = PropertyRef(
        "network_partial_uri",
        description="A partial resource URI of the network this Forwarding Rule belongs to.",
    )
    port_range: PropertyRef = PropertyRef(
        "port_range",
        description="Port range used in conjunction with a target resource. Only packets addressed to ports in the specified range will be forwarded to target configured.",
    )
    ports: PropertyRef = PropertyRef(
        "ports",
        description="Ports to forward to a backend service. Only packets addressed to these ports are forwarded to the backend services configured.",
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="The project ID that this Forwarding Rule belongs to."
    )
    region: PropertyRef = PropertyRef(
        "region", description="The region of this Forwarding Rule."
    )
    self_link: PropertyRef = PropertyRef(
        "self_link", description="Server-defined URL for the resource."
    )
    subnetwork: PropertyRef = PropertyRef(
        "subnetwork_partial_uri",
        description="A partial resource URI of the subnetwork this Forwarding Rule belongs to.",
    )
    target: PropertyRef = PropertyRef(
        "target",
        description="A partial resource URI of the target resource to receive the traffic.",
    )


@dataclass(frozen=True)
class GCPForwardingRuleToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPForwardingRuleToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPForwardingRuleToProjectRelProperties = (
        GCPForwardingRuleToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPForwardingRuleToSubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPForwardingRuleToSubnetRel(CartographyRelSchema):
    target_node_label: str = "GCPSubnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("subnetwork_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPForwardingRuleToSubnetRelProperties = (
        GCPForwardingRuleToSubnetRelProperties()
    )


@dataclass(frozen=True)
class GCPForwardingRuleToVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPForwardingRuleToVpcRel(CartographyRelSchema):
    target_node_label: str = "GCPVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("network_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPForwardingRuleToVpcRelProperties = (
        GCPForwardingRuleToVpcRelProperties()
    )


@dataclass(frozen=True)
class GCPForwardingRuleSchema(CartographyNodeSchema):
    """A Google Cloud forwarding rule that directs traffic to a load balancer target."""

    label: str = "GCPForwardingRule"
    properties: GCPForwardingRuleNodeProperties = GCPForwardingRuleNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["LoadBalancer"])
    sub_resource_relationship: GCPForwardingRuleToProjectRel = (
        GCPForwardingRuleToProjectRel()
    )


# TODO: I don't think we need this schema
@dataclass(frozen=True)
class GCPForwardingRuleWithSubnetSchema(CartographyNodeSchema):
    """A Google Cloud forwarding rule that directs traffic to a load balancer target."""

    label: str = "GCPForwardingRule"
    properties: GCPForwardingRuleNodeProperties = GCPForwardingRuleNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["LoadBalancer"])
    sub_resource_relationship: GCPForwardingRuleToProjectRel = (
        GCPForwardingRuleToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPForwardingRuleToSubnetRel(),
        ]
    )


@dataclass(frozen=True)
class GCPForwardingRuleWithVpcSchema(CartographyNodeSchema):
    """A Google Cloud forwarding rule that directs traffic to a load balancer target."""

    label: str = "GCPForwardingRule"
    properties: GCPForwardingRuleNodeProperties = GCPForwardingRuleNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["LoadBalancer"])
    sub_resource_relationship: GCPForwardingRuleToProjectRel = (
        GCPForwardingRuleToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPForwardingRuleToVpcRel(),
        ]
    )
