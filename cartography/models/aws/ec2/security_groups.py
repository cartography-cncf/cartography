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
class EC2SecurityGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("GroupId", description="Same as `groupid`")
    groupid: PropertyRef = PropertyRef(
        "GroupId",
        extra_index=True,
        description="The ID of the security group. Note that these are globally unique in AWS.",
    )
    name: PropertyRef = PropertyRef(
        "GroupName", description="The name of the security group"
    )
    description: PropertyRef = PropertyRef(
        "Description", description="A description of the security group"
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region this security group is installed in",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class EC2SecurityGroupToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SecurityGroupToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSEC2SecurityGroup`."

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
    "Represents a `MEMBER_OF_EC2_SECURITY_GROUP` relationship from `AWSVpc` to `AWSEC2SecurityGroup`."

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
    "Represents a `ALLOWS_TRAFFIC_FROM` relationship from `AWSEC2SecurityGroup` to `AWSEC2SecurityGroup`."

    target_node_label: str = "AWSEC2SecurityGroup"
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
    "Represents an Amazon EC2 security group."

    label: str = "AWSEC2SecurityGroup"
    properties: EC2SecurityGroupNodeProperties = EC2SecurityGroupNodeProperties()
    # DEPRECATED: legacy EC2SecurityGroup node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["EC2SecurityGroup", "NetworkAccessControl"]
    )
    sub_resource_relationship: EC2SecurityGroupToAWSAccountRel = (
        EC2SecurityGroupToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2SecurityGroupToVpcRel(),
            EC2SecurityGroupToSourceGroupRel(),
        ]
    )
