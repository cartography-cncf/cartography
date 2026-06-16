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
class CircleCIScheduleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    project_slug: PropertyRef = PropertyRef("project_slug")
    actor_login: PropertyRef = PropertyRef("actor_login")
    # ponytail: timetable (per-hour/days-of-week object) flattened out; add the
    # individual cadence fields if scheduled-trigger analysis ever needs them.


@dataclass(frozen=True)
class CircleCIScheduleToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIProject)-[:RESOURCE]->(:CircleCISchedule)
class CircleCIScheduleToProjectRel(CartographyRelSchema):
    target_node_label: str = "CircleCIProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CircleCIScheduleToProjectRelProperties = (
        CircleCIScheduleToProjectRelProperties()
    )


@dataclass(frozen=True)
class CircleCIScheduleSchema(CartographyNodeSchema):
    label: str = "CircleCISchedule"
    properties: CircleCIScheduleNodeProperties = CircleCIScheduleNodeProperties()
    sub_resource_relationship: CircleCIScheduleToProjectRel = (
        CircleCIScheduleToProjectRel()
    )
