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
class AWSIPv4CidrBlockNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    vpcid: PropertyRef = PropertyRef("VpcId")
    association_id: PropertyRef = PropertyRef("AssociationId")
    cidr_block: PropertyRef = PropertyRef("CidrBlock")
    block_state: PropertyRef = PropertyRef("BlockState")
    block_state_message: PropertyRef = PropertyRef("BlockStateMessage")
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


@dataclass(frozen=True)
class AWSIPv4CidrBlockSchema(CartographyNodeSchema):
    """
    There is no sub-resource relationship here because a
    CIDR block can be associated with more than one account
    and it doesn't make sense to scope it to one.
    """

    label: str = "AWSCidrBlock"
    properties: AWSIPv4CidrBlockNodeProperties = AWSIPv4CidrBlockNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [AWSIPv4CidrBlockToAWSVpcRel()]
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["AWSIpv4CidrBlock"])


@dataclass(frozen=True)
class AWSIPv6CidrBlockNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    vpcid: PropertyRef = PropertyRef("VpcId")
    association_id: PropertyRef = PropertyRef("AssociationId")
    cidr_block: PropertyRef = PropertyRef("CidrBlock")
    block_state: PropertyRef = PropertyRef("BlockState")
    block_state_message: PropertyRef = PropertyRef("BlockStateMessage")
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


@dataclass(frozen=True)
class AWSIPv6CidrBlockSchema(CartographyNodeSchema):
    """
    There is no sub-resource relationship here because a
    CIDR block can be associated with more than one account
    and it doesn't make sense to scope it to one.
    """

    label: str = "AWSCidrBlock"
    properties: AWSIPv6CidrBlockNodeProperties = AWSIPv6CidrBlockNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [AWSIPv6CidrBlockToAWSVpcRel()]
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["AWSIpv6CidrBlock"])
