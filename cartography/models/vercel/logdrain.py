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
class VercelLogDrainNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Log drain ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Log drain name."
    )
    url: PropertyRef = PropertyRef("url", description="Log drain destination URL.")
    delivery_format: PropertyRef = PropertyRef(
        "deliveryFormat", description="Format used to deliver logs."
    )
    status: PropertyRef = PropertyRef("status", description="Log drain status.")
    sources: PropertyRef = PropertyRef(
        "sources", description="Log sources delivered by the drain."
    )
    environments: PropertyRef = PropertyRef(
        "environments", description="Environments monitored by the drain."
    )
    project_ids: PropertyRef = PropertyRef(
        "projectIds", description="IDs of projects monitored by the drain."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Timestamp when the log drain was created."
    )


@dataclass(frozen=True)
class VercelLogDrainToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelLogDrain)
class VercelLogDrainToTeamRel(CartographyRelSchema):
    """The Vercel team contains this log drain as a resource."""

    target_node_label: str = "VercelTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TEAM_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelLogDrainToTeamRelProperties = VercelLogDrainToTeamRelProperties()


@dataclass(frozen=True)
class VercelLogDrainToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelLogDrain)-[:MONITORS]->(:VercelProject)
class VercelLogDrainToProjectRel(CartographyRelSchema):
    """The Vercel log drain monitors this project."""

    target_node_label: str = "VercelProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("projectIds", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MONITORS"
    properties: VercelLogDrainToProjectRelProperties = (
        VercelLogDrainToProjectRelProperties()
    )


@dataclass(frozen=True)
class VercelLogDrainSchema(CartographyNodeSchema):
    """A Vercel log delivery drain."""

    label: str = "VercelLogDrain"
    properties: VercelLogDrainNodeProperties = VercelLogDrainNodeProperties()
    sub_resource_relationship: VercelLogDrainToTeamRel = VercelLogDrainToTeamRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelLogDrainToProjectRel()],
    )
