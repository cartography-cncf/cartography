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
class EC2NetworkAclNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Arn")
    arn: PropertyRef = PropertyRef("Arn")
    network_acl_id: PropertyRef = PropertyRef("Id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    is_default: PropertyRef = PropertyRef("IsDefault")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    vpc_id: PropertyRef = PropertyRef("VpcId")


@dataclass(frozen=True)
class EC2NetworkAclToVpcRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkAclToVpcRel(CartographyRelSchema):
    target_node_label: str = "AWSVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"vpcid": PropertyRef("VpcId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_AWS_VPC"
    properties: EC2NetworkAclToVpcRelRelProperties = (
        EC2NetworkAclToVpcRelRelProperties()
    )


@dataclass(frozen=True)
class EC2NetworkAclToSubnetRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkAclToSubnetRel(CartographyRelSchema):
    target_node_label: str = "EC2Subnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"subnetid": PropertyRef("SubnetId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PART_OF_SUBNET"
    properties: EC2NetworkAclToSubnetRelRelProperties = (
        EC2NetworkAclToSubnetRelRelProperties()
    )


@dataclass(frozen=True)
class EC2NetworkAclToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkAclToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2NetworkAclToAWSAccountRelRelProperties = (
        EC2NetworkAclToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class EC2NetworkAclSchema(CartographyNodeSchema):
    """
    Network interface as known by describe-network-interfaces.
    """

    label: str = "EC2NetworkAcl"
    properties: EC2NetworkAclNodeProperties = EC2NetworkAclNodeProperties()
    sub_resource_relationship: EC2NetworkAclToAWSAccountRel = (
        EC2NetworkAclToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2NetworkAclToVpcRel(),
            EC2NetworkAclToSubnetRel(),
        ],
    )
