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
class EventBridgeRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Arn")
    arn: PropertyRef = PropertyRef("Arn", extra_index=True)
    name: PropertyRef = PropertyRef("Name")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    event_pattern: PropertyRef = PropertyRef("EventPattern")
    state: PropertyRef = PropertyRef("State")
    description: PropertyRef = PropertyRef("Description")
    schedule_expression: PropertyRef = PropertyRef("ScheduleExpression")
    role_arn: PropertyRef = PropertyRef("RoleArn")
    managed_by: PropertyRef = PropertyRef("ManagedBy")
    event_bus_name: PropertyRef = PropertyRef("EventBusName")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EventBridgeRuleToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EventBridgeRuleToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EventBridgeRuleToAwsAccountRelProperties = (
        EventBridgeRuleToAwsAccountRelProperties()
    )


@dataclass(frozen=True)
class EventBridgeRuleToAWSRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EventBridgeRuleToAWSRoleRel(CartographyRelSchema):
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("RoleArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: EventBridgeRuleToAWSRoleRelProperties = (
        EventBridgeRuleToAWSRoleRelProperties()
    )


@dataclass(frozen=True)
class EventBridgeRuleSchema(CartographyNodeSchema):
    label: str = "EventBridgeRule"
    properties: EventBridgeRuleNodeProperties = EventBridgeRuleNodeProperties()
    sub_resource_relationship: EventBridgeRuleToAWSAccountRel = (
        EventBridgeRuleToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EventBridgeRuleToAWSRoleRel(),
        ]
    )
