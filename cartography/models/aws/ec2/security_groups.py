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
class EC2SecurityGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("GroupId")
    groupid: PropertyRef = PropertyRef("GroupId", extra_index=True)
    name: PropertyRef = PropertyRef("GroupName")
    description: PropertyRef = PropertyRef("Description")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SecurityGroupToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SecurityGroupToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2SecurityGroupToAWSAccountRelProperties = (
        EC2SecurityGroupToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class EC2SecurityGroupToVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SecurityGroupToVpcRel(CartographyRelSchema):
    target_node_label: str = "AWSVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"vpcid": PropertyRef("VpcId")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF_EC2_SECURITY_GROUP"
    properties: EC2SecurityGroupToVpcRelProperties = (
        EC2SecurityGroupToVpcRelProperties()
    )


@dataclass(frozen=True)
class EC2SecurityGroupToSourceGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SecurityGroupToSourceGroupRel(CartographyRelSchema):
    target_node_label: str = "EC2SecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"groupid": PropertyRef("SOURCE_GROUP_IDS", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ALLOWS_TRAFFIC_FROM"
    properties: EC2SecurityGroupToSourceGroupRelProperties = (
        EC2SecurityGroupToSourceGroupRelProperties()
    )


@dataclass(frozen=True)
class EC2SecurityGroupSchema(CartographyNodeSchema):
    label: str = "EC2SecurityGroup"
    properties: EC2SecurityGroupNodeProperties = EC2SecurityGroupNodeProperties()
    sub_resource_relationship: EC2SecurityGroupToAWSAccountRel = (
        EC2SecurityGroupToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2SecurityGroupToVpcRel(),
            EC2SecurityGroupToSourceGroupRel(),
        ]
    )
