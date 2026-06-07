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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    url: PropertyRef = PropertyRef("url")
    delivery_format: PropertyRef = PropertyRef("deliveryFormat")
    status: PropertyRef = PropertyRef("status")
    sources: PropertyRef = PropertyRef("sources")
    environments: PropertyRef = PropertyRef("environments")
    project_ids: PropertyRef = PropertyRef("projectIds")
    created_at: PropertyRef = PropertyRef("createdAt")


@dataclass(frozen=True)
class VercelLogDrainToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelLogDrain)
class VercelLogDrainToTeamRel(CartographyRelSchema):
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
    label: str = "VercelLogDrain"
    properties: VercelLogDrainNodeProperties = VercelLogDrainNodeProperties()
    sub_resource_relationship: VercelLogDrainToTeamRel = VercelLogDrainToTeamRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelLogDrainToProjectRel()],
    )
