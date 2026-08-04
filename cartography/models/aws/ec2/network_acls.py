from dataclasses import dataclass

from cartography.models.aws.extra_labels import LEGACY_EC2_NETWORK_ACL
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
class EC2NetworkAclNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "Arn", description="Unique identifier for this `AWSEC2NetworkAcl` node."
    )
    arn: PropertyRef = PropertyRef(
        "Arn", description="Amazon Resource Name (ARN) of this `AWSEC2NetworkAcl` node."
    )
    network_acl_id: PropertyRef = PropertyRef(
        "Id",
        description="Identifier of the network ACL linked to this `AWSEC2NetworkAcl` node.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    is_default: PropertyRef = PropertyRef(
        "IsDefault", description="Whether this `AWSEC2NetworkAcl` node default."
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="AWS Region containing this `AWSEC2NetworkAcl` node.",
    )
    vpc_id: PropertyRef = PropertyRef(
        "VpcId",
        description="Identifier of the VPC linked to this `AWSEC2NetworkAcl` node.",
    )


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
    target_node_label: str = "AWSEC2Subnet"
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
    """Representation of an AWS [EC2 Network ACL](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_NetworkAcl.html)"""

    label: str = "AWSEC2NetworkAcl"
    # DEPRECATED: legacy EC2NetworkAcl node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([LEGACY_EC2_NETWORK_ACL])
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
