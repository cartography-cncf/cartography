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
class OpsgenieScheduleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Opsgenie schedule ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Schedule name.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Schedule description.",
    )
    timezone: PropertyRef = PropertyRef(
        "timezone",
        description="Schedule time zone.",
    )
    enabled: PropertyRef = PropertyRef(
        "enabled",
        description="Whether the schedule is enabled.",
    )


@dataclass(frozen=True)
class OpsgenieScheduleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OpsgenieAccountToScheduleRel(CartographyRelSchema):
    """The account contains the schedule."""

    target_node_label: str = "OpsgenieAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpsgenieScheduleRelProperties = OpsgenieScheduleRelProperties()


@dataclass(frozen=True)
class OpsgenieScheduleToTeamRel(CartographyRelSchema):
    """The team owns the schedule."""

    target_node_label: str = "OpsgenieTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_team_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: OpsgenieScheduleRelProperties = OpsgenieScheduleRelProperties()


@dataclass(frozen=True)
class OpsgenieScheduleSchema(CartographyNodeSchema):
    """An on-call schedule in an Opsgenie account."""

    label: str = "OpsgenieSchedule"
    properties: OpsgenieScheduleNodeProperties = OpsgenieScheduleNodeProperties()
    sub_resource_relationship: OpsgenieAccountToScheduleRel = (
        OpsgenieAccountToScheduleRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[OpsgenieScheduleToTeamRel()],
    )
