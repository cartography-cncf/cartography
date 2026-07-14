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
    id: PropertyRef = PropertyRef("id", description="Integration installation ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    slug: PropertyRef = PropertyRef(
        "slug", extra_index=True, description="Integration slug."
    )
    integration_id: PropertyRef = PropertyRef(
        "integrationId", description="Integration marketplace ID."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Integration installation status."
    )
    scopes: PropertyRef = PropertyRef(
        "scopes", description="Scopes granted to the integration."
    )
    project_selection: PropertyRef = PropertyRef(
        "projectSelection", description="Project selection mode for the integration."
    )
    project_ids: PropertyRef = PropertyRef(
        "projects", description="IDs of projects selected for the integration."
    )
    source: PropertyRef = PropertyRef(
        "source", description="Source used to install the integration."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Timestamp when the integration was installed."
    )
    updated_at: PropertyRef = PropertyRef(
        "updatedAt", description="Timestamp when the integration was last updated."
    )


@dataclass(frozen=True)
class VercelIntegrationToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelIntegration)
class VercelIntegrationToTeamRel(CartographyRelSchema):
    """The Vercel team contains this integration as a resource."""

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
    """The Vercel integration is configured for this project."""

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
    """A third-party integration installed for a Vercel team."""

    label: str = "VercelIntegration"
    properties: VercelIntegrationNodeProperties = VercelIntegrationNodeProperties()
    sub_resource_relationship: VercelIntegrationToTeamRel = VercelIntegrationToTeamRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelIntegrationToProjectRel()],
    )
