from dataclasses import dataclass

from cartography.models.aws.ec2.auto_scaling_groups import EC2SubnetToAWSAccountRel
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
class EC2SubnetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("SubnetId", description="same as subnetid")
    subnetid: PropertyRef = PropertyRef(
        "SubnetId", extra_index=True, description="The ID of the subnet"
    )
    subnet_id: PropertyRef = PropertyRef(
        "SubnetId", extra_index=True, description="The ID of the subnet"
    )
    subnet_arn: PropertyRef = PropertyRef(
        "SubnetArn", description="The Amazon Resource Name (ARN) of the subnet"
    )
    name: PropertyRef = PropertyRef(
        "CidrBlock", description="The IPv4 CIDR block assigned to the subnet"
    )
    cidr_block: PropertyRef = PropertyRef(
        "CidrBlock", description="The IPv4 CIDR block assigned to the subnet"
    )
    available_ip_address_count: PropertyRef = PropertyRef(
        "AvailableIpAddressCount",
        description="The number of unused private IPv4 addresses in the subnet. The IPv4 addresses for any stopped instances are considered unavailable",
    )
    default_for_az: PropertyRef = PropertyRef(
        "DefaultForAz",
        description="Indicates whether this is the default subnet for the Availability Zone.",
    )
    map_customer_owned_ip_on_launch: PropertyRef = PropertyRef(
        "MapCustomerOwnedIpOnLaunch",
        description="Indicates whether a network interface created in this subnet (including a network interface created by RunInstances ) receives a customer-owned IPv4 address",
    )
    state: PropertyRef = PropertyRef(
        "State", description="The current state of the subnet."
    )
    assignipv6addressoncreation: PropertyRef = PropertyRef(
        "AssignIpv6AddressOnCreation",
        description="Indicates whether a network interface created in this subnet (including a network interface created by RunInstances ) receives an IPv6 address.",
    )
    map_public_ip_on_launch: PropertyRef = PropertyRef(
        "MapPublicIpOnLaunch",
        description="Indicates whether instances launched in this subnet receive a public IPv4 address",
    )
    availability_zone: PropertyRef = PropertyRef(
        "AvailabilityZone", description="The Availability Zone of the subnet"
    )
    availability_zone_id: PropertyRef = PropertyRef(
        "AvailabilityZoneId", description="The AZ ID of the subnet"
    )
    vpc_id: PropertyRef = PropertyRef(
        "VpcId", description="The ID of the VPC this subnet belongs to"
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region the subnet is installed on",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class EC2SubnetToVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetToVpcRel(CartographyRelSchema):
    "Represents a `MEMBER_OF_AWS_VPC` relationship from `AWSEC2Subnet` to `AWSVpc`."

    target_node_label: str = "AWSVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("VpcId")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_AWS_VPC"
    properties: EC2SubnetToVpcRelProperties = EC2SubnetToVpcRelProperties()


@dataclass(frozen=True)
class EC2SubnetSchema(CartographyNodeSchema):
    "Represents a subnet in an Amazon EC2 virtual private cloud."

    label: str = "AWSEC2Subnet"
    properties: EC2SubnetNodeProperties = EC2SubnetNodeProperties()
    # DEPRECATED: legacy EC2Subnet node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EC2Subnet", "Subnet"])
    sub_resource_relationship: EC2SubnetToAWSAccountRel = EC2SubnetToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2SubnetToVpcRel(),
        ]
    )
