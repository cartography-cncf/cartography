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
class DirectConnectVirtualInterfaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "virtualInterfaceId", description="The ID of the virtual interface"
    )
    virtual_interface_id: PropertyRef = PropertyRef(
        "virtualInterfaceId",
        extra_index=True,
        description="The ID of the virtual interface",
    )
    name: PropertyRef = PropertyRef(
        "virtualInterfaceName", description="The name of the virtual interface"
    )
    type: PropertyRef = PropertyRef(
        "virtualInterfaceType",
        extra_index=True,
        description="The type of virtual interface. Valid values: private, public, transit",
    )
    state: PropertyRef = PropertyRef(
        "virtualInterfaceState",
        description=(
            "The state of the virtual interface. Valid values: confirming, verifying, pending, "
            "available, down, deleting, deleted, rejected, unknown"
        ),
    )
    owner_account: PropertyRef = PropertyRef(
        "ownerAccount", description="The AWS account that owns the virtual interface"
    )
    connection_id: PropertyRef = PropertyRef(
        "connectionId",
        description="The ID of the connection this virtual interface runs on",
    )
    direct_connect_gateway_id: PropertyRef = PropertyRef(
        "directConnectGatewayId",
        description="The ID of the Direct Connect gateway, for transit and private virtual interfaces",
    )
    virtual_gateway_id: PropertyRef = PropertyRef(
        "virtualGatewayId",
        description="The ID of the virtual private gateway, for private virtual interfaces",
    )
    vlan: PropertyRef = PropertyRef("vlan", description="The ID of the VLAN")
    asn: PropertyRef = PropertyRef(
        "asn",
        description="The autonomous system number (ASN) of the customer router for the BGP session",
    )
    amazon_side_asn: PropertyRef = PropertyRef(
        "amazonSideAsn",
        description="The autonomous system number (ASN) of the Amazon side",
    )
    address_family: PropertyRef = PropertyRef(
        "addressFamily",
        description="The address family for the BGP peer. Valid values: ipv4, ipv6",
    )
    amazon_address: PropertyRef = PropertyRef(
        "amazonAddress", description="The IP address assigned to the Amazon interface"
    )
    customer_address: PropertyRef = PropertyRef(
        "customerAddress",
        description="The IP address assigned to the customer interface",
    )
    mtu: PropertyRef = PropertyRef(
        "mtu", description="The maximum transmission unit, in bytes"
    )
    site_link_enabled: PropertyRef = PropertyRef(
        "siteLinkEnabled", description="Indicates whether SiteLink is enabled"
    )
    route_filter_prefixes: PropertyRef = PropertyRef(
        "RouteFilterPrefixes",
        description=(
            "The CIDR prefixes advertised to AWS through this virtual interface. Public virtual "
            "interfaces advertise the customer's public prefixes here"
        ),
    )
    bgp_peer_states: PropertyRef = PropertyRef(
        "BgpPeerStates",
        description="The state of each BGP peer on this virtual interface, as '<bgpPeerId>:<bgpStatus>'",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the virtual interface"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DirectConnectVirtualInterfaceToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DirectConnectVirtualInterfaceToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DirectConnectVirtualInterfaceToAWSAccountRelProperties = (
        DirectConnectVirtualInterfaceToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class VirtualInterfaceToConnectionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class VirtualInterfaceToConnectionRel(CartographyRelSchema):
    target_node_label: str = "AWSDirectConnectConnection"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"connection_id": PropertyRef("connectionId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_ON"
    properties: VirtualInterfaceToConnectionRelProperties = (
        VirtualInterfaceToConnectionRelProperties()
    )


@dataclass(frozen=True)
class VirtualInterfaceToGatewayRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class VirtualInterfaceToGatewayRel(CartographyRelSchema):
    target_node_label: str = "AWSDirectConnectGateway"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("directConnectGatewayId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: VirtualInterfaceToGatewayRelProperties = (
        VirtualInterfaceToGatewayRelProperties()
    )


@dataclass(frozen=True)
class DirectConnectVirtualInterfaceSchema(CartographyNodeSchema):
    """Representation of an AWS [Direct Connect virtual interface](https://docs.aws.amazon.com/directconnect/latest/APIReference/API_VirtualInterface.html): the BGP session that carries traffic over a connection."""

    label: str = "AWSDirectConnectVirtualInterface"
    properties: DirectConnectVirtualInterfaceNodeProperties = (
        DirectConnectVirtualInterfaceNodeProperties()
    )
    sub_resource_relationship: DirectConnectVirtualInterfaceToAWSAccountRel = (
        DirectConnectVirtualInterfaceToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            VirtualInterfaceToConnectionRel(),
            VirtualInterfaceToGatewayRel(),
        ],
    )
