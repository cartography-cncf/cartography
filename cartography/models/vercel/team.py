from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class VercelTeamNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Team ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    name: PropertyRef = PropertyRef("name", description="Team display name.")
    slug: PropertyRef = PropertyRef(
        "slug", extra_index=True, description="URL slug of the team."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Timestamp when the team was created."
    )
    avatar: PropertyRef = PropertyRef("avatar", description="URL of the team avatar.")


@dataclass(frozen=True)
class VercelTeamSchema(CartographyNodeSchema):
    """A Vercel team with the canonical Tenant label."""

    label: str = "VercelTeam"
    properties: VercelTeamNodeProperties = VercelTeamNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
