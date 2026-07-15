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
class EventBridgeRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "Arn", description="System-assigned eventbridge rule ID"
    )
    arn: PropertyRef = PropertyRef(
        "Arn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) of the rule",
    )
    name: PropertyRef = PropertyRef("Name", description="The name of the rule")
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the rule"
    )
    event_pattern: PropertyRef = PropertyRef(
        "EventPattern", description="The event pattern of the rule"
    )
    state: PropertyRef = PropertyRef(
        "State",
        description="The state of the rule, Valid Values: ENABLED, DISABLED, ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS",
    )
    description: PropertyRef = PropertyRef(
        "Description", description="The description of the rule"
    )
    schedule_expression: PropertyRef = PropertyRef(
        "ScheduleExpression", description="The scheduling expression"
    )
    role_arn: PropertyRef = PropertyRef(
        "RoleArn",
        description="The Amazon Resource Name (ARN) of the role that is used for target invocation",
    )
    managed_by: PropertyRef = PropertyRef(
        "ManagedBy",
        description="If the rule was created on behalf of your account by an AWS service, this field displays the principal name of the service that created the rule",
    )
    event_bus_name: PropertyRef = PropertyRef(
        "EventBusName",
        description="The name or ARN of the event bus associated with the rule",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class EventBridgeRuleToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EventBridgeRuleToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSEventBridgeRule`."

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
    "Represents a `ASSOCIATED_WITH` relationship from `AWSEventBridgeRule` to `AWSRole`."

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
    "Represents an `AWSEventBridgeRule` node in the AWS graph."

    label: str = "AWSEventBridgeRule"
    # DEPRECATED: legacy EventBridgeRule node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EventBridgeRule"])
    properties: EventBridgeRuleNodeProperties = EventBridgeRuleNodeProperties()
    sub_resource_relationship: EventBridgeRuleToAWSAccountRel = (
        EventBridgeRuleToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EventBridgeRuleToAWSRoleRel(),
        ]
    )
