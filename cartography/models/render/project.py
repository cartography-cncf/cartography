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
class RenderProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Render project.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the project."
    )
    owner_id: PropertyRef = PropertyRef(
        "ownerId", description="ID of the owning Render workspace."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Time when the project was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updatedAt", description="Time when the project was last modified."
    )


@dataclass(frozen=True)
class RenderProjectToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderTenant)-[:RESOURCE]->(:RenderProject)
class RenderProjectToTenantRel(CartographyRelSchema):
    """Connects a Render workspace to a project that it contains."""

    target_node_label: str = "RenderTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OWNER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RenderProjectToTenantRelProperties = RenderProjectToTenantRelProperties()


@dataclass(frozen=True)
class RenderProjectSchema(CartographyNodeSchema):
    """A Render project: a collection of environments."""

    label: str = "RenderProject"
    properties: RenderProjectNodeProperties = RenderProjectNodeProperties()
    sub_resource_relationship: RenderProjectToTenantRel = RenderProjectToTenantRel()
