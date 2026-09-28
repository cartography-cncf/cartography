from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class RailwayWorkspaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Railway workspace.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Display name of the workspace.",
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt",
        description="Time when the workspace was created.",
    )
    preferred_region: PropertyRef = PropertyRef(
        "preferredRegion",
        description="Default deployment region for new services.",
    )
    project_count: PropertyRef = PropertyRef(
        "projectCount",
        description="Number of projects in the workspace.",
    )
    # Workspace-wide security posture. Both are Pro/Enterprise features and read false on
    # personal and Hobby workspaces.
    has_2fa_enforcement: PropertyRef = PropertyRef(
        "has2FAEnforcement",
        description="Whether the workspace requires two-factor authentication.",
    )
    has_saml: PropertyRef = PropertyRef(
        "hasSAML",
        description="Whether SAML single sign-on is configured.",
    )
    plan: PropertyRef = PropertyRef(
        "plan",
        description="Billing plan for the workspace.",
    )


@dataclass(frozen=True)
class RailwayWorkspaceSchema(CartographyNodeSchema):
    """A Railway workspace that forms a billing, ownership, and access boundary."""

    label: str = "RailwayWorkspace"
    properties: RailwayWorkspaceNodeProperties = RailwayWorkspaceNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
