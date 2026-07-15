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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that updated this `AWSEC2NetworkAcl` node.",
    )
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
    "Represents a `MEMBER_OF_AWS_VPC` relationship from `AWSEC2NetworkAcl` to `AWSVpc`."

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
    "Represents a `PART_OF_SUBNET` relationship from `AWSEC2NetworkAcl` to `AWSEC2Subnet`."

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
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSEC2NetworkAcl`."

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

    label: str = "AWSEC2NetworkAcl"
    # DEPRECATED: legacy EC2NetworkAcl node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EC2NetworkAcl"])
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
