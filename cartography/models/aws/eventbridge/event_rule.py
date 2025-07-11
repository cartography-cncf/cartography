from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class EventRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("arn")
    arn: PropertyRef = PropertyRef("arn", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    name: PropertyRef = PropertyRef("name", extra_index=True)
    state: PropertyRef = PropertyRef("state")
    description: PropertyRef = PropertyRef("description")
    event_pattern: PropertyRef = PropertyRef("event_pattern")
    schedule_expression: PropertyRef = PropertyRef("schedule_expression")
    role_arn: PropertyRef = PropertyRef("role_arn")
    event_bus_name: PropertyRef = PropertyRef("event_bus_name", extra_index=True)
    managed_by: PropertyRef = PropertyRef("managed_by")
    created_by: PropertyRef = PropertyRef("created_by")

    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)


@dataclass(frozen=True)
class EventRuleToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EventRuleToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EventRuleToAWSAccountRelProperties = (
        EventRuleToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class EventRuleSchema(CartographyNodeSchema):
    label: str = "EventRule"
    properties: EventRuleNodeProperties = EventRuleNodeProperties()
    sub_resource_relationship: EventRuleToAWSAccountRel = EventRuleToAWSAccountRel()
