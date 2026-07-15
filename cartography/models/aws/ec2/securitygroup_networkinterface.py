from dataclasses import dataclass

from cartography.models.aws.ec2.securitygroup_instance import (
    EC2SecurityGroupToAWSAccountRel,
)
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
class EC2SecurityGroupNetworkInterfaceNodeProperties(CartographyNodeProperties):
    # arn: PropertyRef = PropertyRef('Arn', extra_index=True) # TODO use arn; issue #1024
    id: PropertyRef = PropertyRef("GroupId", description="Same as `groupid`")
    groupid: PropertyRef = PropertyRef(
        "GroupId",
        extra_index=True,
        description="The ID of the security group. Note that these are globally unique in AWS.",
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
class EC2SubnetToNetworkInterfaceRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SecurityGroupToNetworkInterfaceRel(CartographyRelSchema):
    "Represents a `MEMBER_OF_EC2_SECURITY_GROUP` relationship from `AWSNetworkInterface` to `AWSEC2SecurityGroup`."

    target_node_label: str = "AWSNetworkInterface"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NetworkInterfaceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF_EC2_SECURITY_GROUP"
    properties: EC2SubnetToNetworkInterfaceRelRelProperties = (
        EC2SubnetToNetworkInterfaceRelRelProperties()
    )


@dataclass(frozen=True)
class EC2SecurityGroupNetworkInterfaceSchema(CartographyNodeSchema):
    "Represents an Amazon EC2 security group."

    # Implementation note:
    # Security groups as known by describe-network-interfaces.

    label: str = "AWSEC2SecurityGroup"
    # DEPRECATED: legacy EC2SecurityGroup node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EC2SecurityGroup"])
    properties: EC2SecurityGroupNetworkInterfaceNodeProperties = (
        EC2SecurityGroupNetworkInterfaceNodeProperties()
    )
    sub_resource_relationship: EC2SecurityGroupToAWSAccountRel = (
        EC2SecurityGroupToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2SecurityGroupToNetworkInterfaceRel(),
        ],
    )
