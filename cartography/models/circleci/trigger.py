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
    id: PropertyRef = PropertyRef("id", description="CircleCI trigger ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    event_name: PropertyRef = PropertyRef(
        "event_name", extra_index=True, description="Event that activates the trigger."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Trigger description."
    )
    event_preset: PropertyRef = PropertyRef(
        "event_preset", description="Configured event preset."
    )
    event_source_provider: PropertyRef = PropertyRef(
        "event_source_provider", description="Provider that supplies trigger events."
    )
    # Set when the trigger is a schedule (provider == "schedule"); this is how
    # scheduled pipeline runs are modelled in CircleCI's current pipeline API.
    cron_expression: PropertyRef = PropertyRef(
        "cron_expression", description="Cron expression for a scheduled trigger."
    )
    checkout_ref: PropertyRef = PropertyRef(
        "checkout_ref", description="Version control reference to check out."
    )
    config_ref: PropertyRef = PropertyRef(
        "config_ref", description="Version control reference containing the config."
    )
    disabled: PropertyRef = PropertyRef(
        "disabled", description="Whether the trigger is disabled."
    )
    pipeline_id: PropertyRef = PropertyRef(
        "pipeline_id", description="ID of the owning CircleCI pipeline."
    )


@dataclass(frozen=True)
class CircleCITriggerToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIProject)-[:RESOURCE]->(:CircleCITrigger)
class CircleCITriggerToProjectRel(CartographyRelSchema):
    """The CircleCI project contains the trigger."""

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
    """The CircleCI pipeline has the trigger."""

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
    """An event or schedule trigger attached to a CircleCI pipeline."""

    label: str = "CircleCITrigger"
    properties: CircleCITriggerNodeProperties = CircleCITriggerNodeProperties()
    sub_resource_relationship: CircleCITriggerToProjectRel = (
        CircleCITriggerToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [CircleCITriggerToPipelineRel()],
    )
