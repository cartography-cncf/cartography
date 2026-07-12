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
class CircleCITriggerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    event_name: PropertyRef = PropertyRef("event_name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    event_preset: PropertyRef = PropertyRef("event_preset")
    event_source_provider: PropertyRef = PropertyRef("event_source_provider")
    # Set when the trigger is a schedule (provider == "schedule"); this is how
    # scheduled pipeline runs are modelled in CircleCI's current pipeline API.
    cron_expression: PropertyRef = PropertyRef("cron_expression")
    checkout_ref: PropertyRef = PropertyRef("checkout_ref")
    config_ref: PropertyRef = PropertyRef("config_ref")
    disabled: PropertyRef = PropertyRef("disabled")
    pipeline_id: PropertyRef = PropertyRef("pipeline_id")


@dataclass(frozen=True)
class CircleCITriggerToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIProject)-[:RESOURCE]->(:CircleCITrigger)
class CircleCITriggerToProjectRel(CartographyRelSchema):
    target_node_label: str = "CircleCIProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CircleCITriggerToProjectRelProperties = (
        CircleCITriggerToProjectRelProperties()
    )


@dataclass(frozen=True)
class CircleCITriggerToPipelineRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIPipeline)-[:HAS_TRIGGER]->(:CircleCITrigger)
class CircleCITriggerToPipelineRel(CartographyRelSchema):
    target_node_label: str = "CircleCIPipeline"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("pipeline_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_TRIGGER"
    properties: CircleCITriggerToPipelineRelProperties = (
        CircleCITriggerToPipelineRelProperties()
    )


@dataclass(frozen=True)
class CircleCITriggerSchema(CartographyNodeSchema):
    label: str = "CircleCITrigger"
    properties: CircleCITriggerNodeProperties = CircleCITriggerNodeProperties()
    sub_resource_relationship: CircleCITriggerToProjectRel = (
        CircleCITriggerToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [CircleCITriggerToPipelineRel()],
    )
