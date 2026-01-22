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
    id: PropertyRef = PropertyRef("RuleId")
    ruleid: PropertyRef = PropertyRef("RuleId", extra_index=True)
    groupid: PropertyRef = PropertyRef("GroupId", extra_index=True)
    protocol: PropertyRef = PropertyRef("Protocol")
    fromport: PropertyRef = PropertyRef("FromPort")
    toport: PropertyRef = PropertyRef("ToPort")
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
    target_node_label: str = "EC2SecurityGroup"
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
    id: PropertyRef = PropertyRef("RangeId")
    range: PropertyRef = PropertyRef("RangeId")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class IpRangeToIpRuleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class IpRangeToIpRuleRel(CartographyRelSchema):
    target_node_label: str = "IpRule"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ruleid": PropertyRef("RuleId")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_IP_RULE"
    properties: IpRangeToIpRuleRelProperties = IpRangeToIpRuleRelProperties()


@dataclass(frozen=True)
class IpRuleSchema(CartographyNodeSchema):
    label: str = "IpRule"
    properties: IpRuleNodeProperties = IpRuleNodeProperties()
    sub_resource_relationship: IpRuleToAWSAccountRel = IpRuleToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [IpRuleToSecurityGroupRel()]
    )


@dataclass(frozen=True)
class IpPermissionInboundSchema(CartographyNodeSchema):
    label: str = "IpRule"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["IpPermissionInbound"])
    properties: IpRuleNodeProperties = IpRuleNodeProperties()
    sub_resource_relationship: IpRuleToAWSAccountRel = IpRuleToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [IpRuleToSecurityGroupRel()]
    )


@dataclass(frozen=True)
class IpRangeSchema(CartographyNodeSchema):
    label: str = "IpRange"
    properties: IpRangeNodeProperties = IpRangeNodeProperties()
    sub_resource_relationship: IpRuleToAWSAccountRel = IpRuleToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships([IpRangeToIpRuleRel()])
