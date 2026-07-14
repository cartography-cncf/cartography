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
class PagerDutyScheduleLayerProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("_layer_id", description="Schedule layer ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    name: PropertyRef = PropertyRef("name", description="Schedule layer name.")
    schedule_id: PropertyRef = PropertyRef(
        "_schedule_id", description="ID of the schedule containing this layer."
    )
    start: PropertyRef = PropertyRef(
        "start", description="Timestamp when the schedule layer starts."
    )
    end: PropertyRef = PropertyRef(
        "end", description="Timestamp when the schedule layer ends, if set."
    )
    rotation_virtual_start: PropertyRef = PropertyRef(
        "rotation_virtual_start",
        description="Effective start timestamp for the layer rotation.",
    )
    rotation_turn_length_seconds: PropertyRef = PropertyRef(
        "rotation_turn_length_seconds",
        description="Duration of each on-call shift in seconds.",
    )


@dataclass(frozen=True)
class PagerDutyScheduleLayerToScheduleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PagerDutySchedule)-[:HAS_LAYER]->(:PagerDutyScheduleLayer)
class PagerDutyScheduleLayerToScheduleRel(CartographyRelSchema):
    """The schedule that contains this layer."""

    target_node_label: str = "PagerDutySchedule"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_schedule_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_LAYER"
    properties: PagerDutyScheduleLayerToScheduleRelProperties = (
        PagerDutyScheduleLayerToScheduleRelProperties()
    )


@dataclass(frozen=True)
class PagerDutyScheduleLayerToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PagerDutyUser)-[:MEMBER_OF]->(:PagerDutyScheduleLayer)
class PagerDutyScheduleLayerToUserRel(CartographyRelSchema):
    """A user who is a member of a schedule layer."""

    target_node_label: str = "PagerDutyUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("users_id", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: PagerDutyScheduleLayerToUserRelProperties = (
        PagerDutyScheduleLayerToUserRelProperties()
    )


@dataclass(frozen=True)
class PagerDutyScheduleLayerSchema(CartographyNodeSchema):
    """A rotation layer within a PagerDuty schedule."""

    label: str = "PagerDutyScheduleLayer"
    properties: PagerDutyScheduleLayerProperties = PagerDutyScheduleLayerProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        [
            PagerDutyScheduleLayerToScheduleRel(),
            PagerDutyScheduleLayerToUserRel(),
        ]
    )
