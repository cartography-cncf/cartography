from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class RailwayWorkspaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    created_at: PropertyRef = PropertyRef("createdAt")
    preferred_region: PropertyRef = PropertyRef("preferredRegion")
    project_count: PropertyRef = PropertyRef("projectCount")
    # Workspace-wide security posture. Both are Pro/Enterprise features and read false on
    # personal and Hobby workspaces.
    has_2fa_enforcement: PropertyRef = PropertyRef("has2FAEnforcement")
    has_saml: PropertyRef = PropertyRef("hasSAML")
    plan: PropertyRef = PropertyRef("plan")


@dataclass(frozen=True)
class RailwayWorkspaceSchema(CartographyNodeSchema):
    label: str = "RailwayWorkspace"
    properties: RailwayWorkspaceNodeProperties = RailwayWorkspaceNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
