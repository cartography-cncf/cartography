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
class EventTargetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    target_id: PropertyRef = PropertyRef("Id")
    target_arn: PropertyRef = PropertyRef("Arn", extra_index=True)
    rule_arn: PropertyRef = PropertyRef("RuleArn", extra_index=True)
    role_arn: PropertyRef = PropertyRef("RoleArn")
    input: PropertyRef = PropertyRef("Input")
    input_path: PropertyRef = PropertyRef("InputPath")

    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)


@dataclass(frozen=True)
class _EventTargetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EventTargetToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: _EventTargetRelProperties = _EventTargetRelProperties()


@dataclass(frozen=True)
class EventTargetToEventRuleRel(CartographyRelSchema):
    target_node_label: str = "EventRule"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("RuleArn")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_TARGET"
    properties: _EventTargetRelProperties = _EventTargetRelProperties()


@dataclass(frozen=True)
class EventTargetSchema(CartographyNodeSchema):
    label: str = "EventTarget"
    properties: EventTargetNodeProperties = EventTargetNodeProperties()
    sub_resource_relationship: EventTargetToAWSAccountRel = EventTargetToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [EventTargetToEventRuleRel()]
    )
