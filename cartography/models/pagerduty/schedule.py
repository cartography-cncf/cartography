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
class PagerDutyScheduleProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Schedule ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    html_url: PropertyRef = PropertyRef(
        "html_url", description="PagerDuty web URL for the schedule."
    )
    type: PropertyRef = PropertyRef(
        "type", description="PagerDuty object type for the schedule."
    )
    summary: PropertyRef = PropertyRef(
        "summary", description="Short summary of the schedule."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Schedule name."
    )
    time_zone: PropertyRef = PropertyRef(
        "time_zone", description="Time zone used by the schedule."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Schedule description."
    )


@dataclass(frozen=True)
class PagerDutyScheduleToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PagerDutyUser)-[:MEMBER_OF]->(:PagerDutySchedule)
class PagerDutyScheduleToUserRel(CartographyRelSchema):
    """A user who is a member of a schedule."""

    target_node_label: str = "PagerDutyUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("users_id", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: PagerDutyScheduleToUserRelProperties = (
        PagerDutyScheduleToUserRelProperties()
    )


@dataclass(frozen=True)
class PagerDutyScheduleSchema(CartographyNodeSchema):
    """A PagerDuty on-call schedule."""

    label: str = "PagerDutySchedule"
    properties: PagerDutyScheduleProperties = PagerDutyScheduleProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        [
            PagerDutyScheduleToUserRel(),
        ]
    )
