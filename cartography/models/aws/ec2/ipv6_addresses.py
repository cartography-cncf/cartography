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
class EC2Ipv6AddressNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Ipv6Address")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    ipv6_address: PropertyRef = PropertyRef("Ipv6Address", extra_index=True)
    network_interface_id: PropertyRef = PropertyRef("NetworkInterfaceId")
    primary: PropertyRef = PropertyRef("IsPrimaryIpv6")


@dataclass(frozen=True)
class EC2Ipv6AddressToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2Ipv6AddressToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2Ipv6AddressToAWSAccountRelProperties = (
        EC2Ipv6AddressToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class EC2Ipv6AddressToNetworkInterfaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2Ipv6AddressToNetworkInterfaceRel(CartographyRelSchema):
    target_node_label: str = "NetworkInterface"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NetworkInterfaceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "IPV6_ADDRESS"
    properties: EC2Ipv6AddressToNetworkInterfaceRelProperties = (
        EC2Ipv6AddressToNetworkInterfaceRelProperties()
    )


@dataclass(frozen=True)
class EC2Ipv6AddressSchema(CartographyNodeSchema):
    label: str = "EC2Ipv6Address"
    # The Ip extra label allows AWSDNSRecord AAAA records to reach this node
    # via the existing DNS_POINTS_TO -> Ip relationship, matching on id (the IPv6 address).
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Ip"])
    properties: EC2Ipv6AddressNodeProperties = EC2Ipv6AddressNodeProperties()
    sub_resource_relationship: EC2Ipv6AddressToAWSAccountRel = (
        EC2Ipv6AddressToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2Ipv6AddressToNetworkInterfaceRel(),
        ],
    )
