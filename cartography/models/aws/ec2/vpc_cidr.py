from dataclasses import dataclass

from cartography.models.aws.extra_labels import AWS_IPV4_CIDR_BLOCK
from cartography.models.aws.extra_labels import AWS_IPV6_CIDR_BLOCK
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
class AWSIPv4CidrBlockNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "Id", description="Unique identifier for this `AWSCidrBlock` node."
    )
    vpcid: PropertyRef = PropertyRef(
        "VpcId",
        description="Identifier of the VPC linked to this `AWSCidrBlock` node.",
    )
    association_id: PropertyRef = PropertyRef(
        "AssociationId",
        description="Identifier of the association linked to this `AWSCidrBlock` node.",
    )
    cidr_block: PropertyRef = PropertyRef(
        "CidrBlock", description="IPv4 or IPv6 CIDR range associated with the VPC."
    )
    block_state: PropertyRef = PropertyRef(
        "BlockState",
        description="State of the CIDR block association, for example ``associating | associated | failing | failed``.",
    )
    block_state_message: PropertyRef = PropertyRef(
        "BlockStateMessage",
        description="Message giving more information about the CIDR block association state.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSIPv4CidrBlockToAWSVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSIPv4CidrBlockToAWSVpcRel(CartographyRelSchema):
    target_node_label: str = "AWSVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("VpcId")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "BLOCK_ASSOCIATION"
    properties: AWSIPv4CidrBlockToAWSVpcRelProperties = (
        AWSIPv4CidrBlockToAWSVpcRelProperties()
    )


# No sub-resource relationship: a CIDR block can be associated with more than one
# account, so scoping it to a single one would be wrong.
@dataclass(frozen=True)
class AWSIPv4CidrBlockSchema(CartographyNodeSchema):
    """An IPv4 [CIDR block used in VPC configuration](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_VpcCidrBlockAssociation.html), associated with a VPC and also labeled `AWSIpv4CidrBlock`."""

    label: str = "AWSCidrBlock"
    properties: AWSIPv4CidrBlockNodeProperties = AWSIPv4CidrBlockNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [AWSIPv4CidrBlockToAWSVpcRel()]
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([AWS_IPV4_CIDR_BLOCK])


@dataclass(frozen=True)
class AWSIPv6CidrBlockNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "Id", description="Unique identifier for this `AWSCidrBlock` node."
    )
    vpcid: PropertyRef = PropertyRef(
        "VpcId",
        description="Identifier of the VPC linked to this `AWSCidrBlock` node.",
    )
    association_id: PropertyRef = PropertyRef(
        "AssociationId",
        description="Identifier of the association linked to this `AWSCidrBlock` node.",
    )
    cidr_block: PropertyRef = PropertyRef(
        "CidrBlock", description="IPv4 or IPv6 CIDR range associated with the VPC."
    )
    block_state: PropertyRef = PropertyRef(
        "BlockState",
        description="State of the CIDR block association, for example ``associating | associated | failing | failed``.",
    )
    block_state_message: PropertyRef = PropertyRef(
        "BlockStateMessage",
        description="Message giving more information about the CIDR block association state.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSIPv6CidrBlockToAWSVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSIPv6CidrBlockToAWSVpcRel(CartographyRelSchema):
    target_node_label: str = "AWSVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("VpcId")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "BLOCK_ASSOCIATION"
    properties: AWSIPv6CidrBlockToAWSVpcRelProperties = (
        AWSIPv6CidrBlockToAWSVpcRelProperties()
    )


# No sub-resource relationship: a CIDR block can be associated with more than one
# account, so scoping it to a single one would be wrong.
@dataclass(frozen=True)
class AWSIPv6CidrBlockSchema(CartographyNodeSchema):
    """An IPv6 [CIDR block used in VPC configuration](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_VpcCidrBlockAssociation.html), associated with a VPC and also labeled `AWSIpv6CidrBlock`."""

    label: str = "AWSCidrBlock"
    properties: AWSIPv6CidrBlockNodeProperties = AWSIPv6CidrBlockNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [AWSIPv6CidrBlockToAWSVpcRel()]
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([AWS_IPV6_CIDR_BLOCK])
