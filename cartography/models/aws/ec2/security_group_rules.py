from dataclasses import dataclass

from cartography.models.aws.extra_labels import AWS_IP_RULE
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
from cartography.models.extra_labels import IP_PERMISSION_INBOUND
from cartography.models.extra_labels import IP_RANGE
from cartography.models.extra_labels import IP_RULE


@dataclass(frozen=True)
class IpRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "RuleId", description="Unique identifier for this `AWSIpRule` node."
    )
    ruleid: PropertyRef = PropertyRef(
        "RuleId",
        extra_index=True,
        description="Identifier of the ruleid linked to this `AWSIpRule` node.",
    )
    groupid: PropertyRef = PropertyRef(
        "GroupId",
        extra_index=True,
        description="Identifier of the group linked to this `AWSIpRule` node.",
    )
    protocol: PropertyRef = PropertyRef(
        "Protocol", description="IP protocol matched by the security-group rule."
    )
    fromport: PropertyRef = PropertyRef(
        "FromPort",
        description="Lowest transport-layer port allowed by the security-group rule.",
    )
    toport: PropertyRef = PropertyRef(
        "ToPort",
        description="Highest transport-layer port allowed by the security-group rule.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class IpRuleToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class IpRuleToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: IpRuleToAWSAccountRelProperties = IpRuleToAWSAccountRelProperties()


@dataclass(frozen=True)
class IpRuleToSecurityGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class IpRuleToSecurityGroupRel(CartographyRelSchema):
    target_node_label: str = "AWSEC2SecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"groupid": PropertyRef("GroupId")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_EC2_SECURITY_GROUP"
    properties: IpRuleToSecurityGroupRelProperties = (
        IpRuleToSecurityGroupRelProperties()
    )


@dataclass(frozen=True)
class IpRangeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "RangeId", description="Unique identifier for this `AWSIpRange` node."
    )
    range: PropertyRef = PropertyRef(
        "RangeId",
        description="Stable identifier derived from the security-group rule IP range.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class IpRangeToIpRuleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class IpRangeToIpRuleRel(CartographyRelSchema):
    target_node_label: str = "AWSIpRule"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ruleid": PropertyRef("RuleId")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_IP_RULE"
    properties: IpRangeToIpRuleRelProperties = IpRangeToIpRuleRelProperties()


@dataclass(frozen=True)
class IpRuleSchema(CartographyNodeSchema):
    """Represents a generic IP rule.  The creation of this node is currently derived from ingesting `AWSEC2SecurityGroup` rules."""

    label: str = "AWSIpRule"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([IP_RULE])
    properties: IpRuleNodeProperties = IpRuleNodeProperties()
    sub_resource_relationship: IpRuleToAWSAccountRel = IpRuleToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [IpRuleToSecurityGroupRel()]
    )


@dataclass(frozen=True)
class IpPermissionInboundSchema(CartographyNodeSchema):
    """An AWSIpPermissionInbound node is a specific type of AWSIpRule. It represents inbound IP-based rules derived from `AWSEC2SecurityGroup` rules."""

    label: str = "AWSIpPermissionInbound"
    # Keep AWSIpRule as an extra label so inbound rules are still queryable as
    # the broader AWSIpRule type while preserving a provider-specific primary label.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [IP_PERMISSION_INBOUND, IP_RULE, AWS_IP_RULE]
    )
    properties: IpRuleNodeProperties = IpRuleNodeProperties()
    sub_resource_relationship: IpRuleToAWSAccountRel = IpRuleToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [IpRuleToSecurityGroupRel()]
    )


@dataclass(frozen=True)
class IpRangeSchema(CartographyNodeSchema):
    """Represents an IP address range (CIDR block) associated with an EC2 Security Group rule. IpRange nodes define the source or destination IP addresses that a security group rule applies to."""

    label: str = "AWSIpRange"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([IP_RANGE])
    properties: IpRangeNodeProperties = IpRangeNodeProperties()
    sub_resource_relationship: IpRuleToAWSAccountRel = IpRuleToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships([IpRangeToIpRuleRel()])
