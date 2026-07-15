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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that updated this `AWSIpRule` node.",
    )


@dataclass(frozen=True)
class IpRuleToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class IpRuleToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSIpPermissionInbound` or `AWSIpRange` or `AWSIpRule`."

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
    "Represents a `MEMBER_OF_EC2_SECURITY_GROUP` relationship from `AWSIpPermissionInbound` or `AWSIpRule` to `AWSEC2SecurityGroup`."

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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that updated this `AWSIpRange` node.",
    )


@dataclass(frozen=True)
class IpRangeToIpRuleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class IpRangeToIpRuleRel(CartographyRelSchema):
    "Represents a `MEMBER_OF_IP_RULE` relationship from `AWSIpRange` to `AWSIpRule`."

    target_node_label: str = "AWSIpRule"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ruleid": PropertyRef("RuleId")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_IP_RULE"
    properties: IpRangeToIpRuleRelProperties = IpRangeToIpRuleRelProperties()


@dataclass(frozen=True)
class IpRuleSchema(CartographyNodeSchema):
    "Represents an `AWSIpRule` node in the AWS graph."

    label: str = "AWSIpRule"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["IpRule"])
    properties: IpRuleNodeProperties = IpRuleNodeProperties()
    sub_resource_relationship: IpRuleToAWSAccountRel = IpRuleToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [IpRuleToSecurityGroupRel()]
    )


@dataclass(frozen=True)
class IpPermissionInboundSchema(CartographyNodeSchema):
    "Represents an `AWSIpPermissionInbound` node in the AWS graph."

    label: str = "AWSIpPermissionInbound"
    # Keep AWSIpRule as an extra label so inbound rules are still queryable as
    # the broader AWSIpRule type while preserving a provider-specific primary label.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["IpPermissionInbound", "IpRule", "AWSIpRule"]
    )
    properties: IpRuleNodeProperties = IpRuleNodeProperties()
    sub_resource_relationship: IpRuleToAWSAccountRel = IpRuleToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [IpRuleToSecurityGroupRel()]
    )


@dataclass(frozen=True)
class IpRangeSchema(CartographyNodeSchema):
    "Represents an `AWSIpRange` node in the AWS graph."

    label: str = "AWSIpRange"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["IpRange"])
    properties: IpRangeNodeProperties = IpRangeNodeProperties()
    sub_resource_relationship: IpRuleToAWSAccountRel = IpRuleToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships([IpRangeToIpRuleRel()])
