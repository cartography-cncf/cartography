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
class RenderEnvironmentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Render environment.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the environment."
    )
    project_id: PropertyRef = PropertyRef(
        "projectId", extra_index=True, description="ID of the owning project."
    )
    owner_id: PropertyRef = PropertyRef(
        "ownerId", description="ID of the owning Render workspace."
    )
    protected_status: PropertyRef = PropertyRef(
        "protectedStatus",
        description="Whether the environment is protected from destructive actions.",
    )
    network_isolation_enabled: PropertyRef = PropertyRef(
        "networkIsolationEnabled",
        description="Whether network isolation is enabled for resources in this environment.",
    )


@dataclass(frozen=True)
class RenderEnvironmentToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderTenant)-[:RESOURCE]->(:RenderEnvironment)
class RenderEnvironmentToTenantRel(CartographyRelSchema):
    """Connects a Render workspace to an environment that it contains."""

    target_node_label: str = "RenderTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OWNER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RenderEnvironmentToTenantRelProperties = (
        RenderEnvironmentToTenantRelProperties()
    )


@dataclass(frozen=True)
class RenderEnvironmentToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderProject)-[:CONTAINS]->(:RenderEnvironment)
class RenderEnvironmentToProjectRel(CartographyRelSchema):
    """Connects a Render project to an environment that it contains."""

    target_node_label: str = "RenderProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("projectId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: RenderEnvironmentToProjectRelProperties = (
        RenderEnvironmentToProjectRelProperties()
    )


@dataclass(frozen=True)
class RenderEnvironmentSchema(CartographyNodeSchema):
    """A Render deployment environment within a project."""

    label: str = "RenderEnvironment"
    properties: RenderEnvironmentNodeProperties = RenderEnvironmentNodeProperties()
    sub_resource_relationship: RenderEnvironmentToTenantRel = (
        RenderEnvironmentToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [RenderEnvironmentToProjectRel()],
    )
