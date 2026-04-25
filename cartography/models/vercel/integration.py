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
class VercelIntegrationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    slug: PropertyRef = PropertyRef("slug", extra_index=True)
    integration_id: PropertyRef = PropertyRef("integrationId")
    status: PropertyRef = PropertyRef("status")
    scopes: PropertyRef = PropertyRef("scopes")
    project_selection: PropertyRef = PropertyRef("projectSelection")
    project_ids: PropertyRef = PropertyRef("projects")
    source: PropertyRef = PropertyRef("source")
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")


@dataclass(frozen=True)
class VercelIntegrationToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelIntegration)
class VercelIntegrationToTeamRel(CartographyRelSchema):
    target_node_label: str = "VercelTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TEAM_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelIntegrationToTeamRelProperties = (
        VercelIntegrationToTeamRelProperties()
    )


@dataclass(frozen=True)
class VercelIntegrationToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelIntegration)-[:CONFIGURED_FOR]->(:VercelProject)
class VercelIntegrationToProjectRel(CartographyRelSchema):
    target_node_label: str = "VercelProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("projects", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONFIGURED_FOR"
    properties: VercelIntegrationToProjectRelProperties = (
        VercelIntegrationToProjectRelProperties()
    )


@dataclass(frozen=True)
class VercelIntegrationSchema(CartographyNodeSchema):
    label: str = "VercelIntegration"
    properties: VercelIntegrationNodeProperties = VercelIntegrationNodeProperties()
    sub_resource_relationship: VercelIntegrationToTeamRel = VercelIntegrationToTeamRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelIntegrationToProjectRel()],
    )
