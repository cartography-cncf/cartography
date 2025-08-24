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
class EventBridgeTargetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    arn: PropertyRef = PropertyRef("Arn", extra_index=True)
    rule_arn: PropertyRef = PropertyRef("RuleArn")
    role_arn: PropertyRef = PropertyRef("RoleArn")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EventBridgeTargetToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EventBridgeTargetToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EventBridgeTargetToAwsAccountRelProperties = (
        EventBridgeTargetToAwsAccountRelProperties()
    )


@dataclass(frozen=True)
class EventBridgeTargetToEventBridgeRuleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EventBridgeTargetToEventBridgeRuleRel(CartographyRelSchema):
    target_node_label: str = "EventBridgeRule"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("RuleArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "LINKED_TO_RULE"
    properties: EventBridgeTargetToEventBridgeRuleRelProperties = (
        EventBridgeTargetToEventBridgeRuleRelProperties()
    )


@dataclass(frozen=True)
class EventBridgeTargetSchema(CartographyNodeSchema):
    label: str = "EventBridgeTarget"
    properties: EventBridgeTargetNodeProperties = EventBridgeTargetNodeProperties()
    sub_resource_relationship: EventBridgeTargetToAWSAccountRel = (
        EventBridgeTargetToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EventBridgeTargetToEventBridgeRuleRel(),
        ]
    )
