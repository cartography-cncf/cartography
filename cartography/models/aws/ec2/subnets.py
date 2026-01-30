from dataclasses import dataclass

from cartography.models.aws.ec2.auto_scaling_groups import EC2SubnetToAWSAccountRel
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
class EC2SubnetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("SubnetId")
    subnetid: PropertyRef = PropertyRef("SubnetId", extra_index=True)
    subnet_id: PropertyRef = PropertyRef("SubnetId", extra_index=True)
    subnet_arn: PropertyRef = PropertyRef("SubnetArn")
    name: PropertyRef = PropertyRef("CidrBlock")
    cidr_block: PropertyRef = PropertyRef("CidrBlock")
    available_ip_address_count: PropertyRef = PropertyRef("AvailableIpAddressCount")
    default_for_az: PropertyRef = PropertyRef("DefaultForAz")
    map_customer_owned_ip_on_launch: PropertyRef = PropertyRef(
        "MapCustomerOwnedIpOnLaunch"
    )
    state: PropertyRef = PropertyRef("State")
    assignipv6addressoncreation: PropertyRef = PropertyRef(
        "AssignIpv6AddressOnCreation"
    )
    map_public_ip_on_launch: PropertyRef = PropertyRef("MapPublicIpOnLaunch")
    availability_zone: PropertyRef = PropertyRef("AvailabilityZone")
    availability_zone_id: PropertyRef = PropertyRef("AvailabilityZoneId")
    vpc_id: PropertyRef = PropertyRef("VpcId")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetToVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetToVpcRel(CartographyRelSchema):
    target_node_label: str = "AWSVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("VpcId")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_AWS_VPC"
    properties: EC2SubnetToVpcRelProperties = EC2SubnetToVpcRelProperties()


@dataclass(frozen=True)
class EC2SubnetSchema(CartographyNodeSchema):
    label: str = "EC2Subnet"
    properties: EC2SubnetNodeProperties = EC2SubnetNodeProperties()
    sub_resource_relationship: EC2SubnetToAWSAccountRel = EC2SubnetToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2SubnetToVpcRel(),
        ]
    )
