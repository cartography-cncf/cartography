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
    id: PropertyRef = PropertyRef(
        "Ipv6Address",
        description="Same as `ipv6_address` \u2014 the IPv6 address string",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The AWS region"
    )
    ipv6_address: PropertyRef = PropertyRef(
        "Ipv6Address",
        extra_index=True,
        description="The IPv6 address (e.g. `2001:db8::1`)",
    )
    network_interface_id: PropertyRef = PropertyRef(
        "NetworkInterfaceId",
        description="The ID of the network interface this address is assigned to",
    )
    primary: PropertyRef = PropertyRef(
        "IsPrimaryIpv6",
        description="`true` if this is the primary IPv6 address on the interface (`IsPrimaryIpv6`), `false` otherwise",
    )


@dataclass(frozen=True)
class EC2Ipv6AddressToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2Ipv6AddressToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSEC2Ipv6Address`."

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
    "Represents a `IPV6_ADDRESS` relationship from `AWSNetworkInterface` to `AWSEC2Ipv6Address`."

    target_node_label: str = "AWSNetworkInterface"
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
    "Represents an `AWSEC2Ipv6Address` node in the AWS graph."

    label: str = "AWSEC2Ipv6Address"
    # The Ip extra label allows AWSDNSRecord AAAA records to reach this node
    # via the existing DNS_POINTS_TO -> Ip relationship, matching on id (the IPv6 address).
    # DEPRECATED: legacy EC2Ipv6Address node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EC2Ipv6Address", "Ip"])
    properties: EC2Ipv6AddressNodeProperties = EC2Ipv6AddressNodeProperties()
    sub_resource_relationship: EC2Ipv6AddressToAWSAccountRel = (
        EC2Ipv6AddressToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2Ipv6AddressToNetworkInterfaceRel(),
        ],
    )
