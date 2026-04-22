from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class VercelTeamNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    slug: PropertyRef = PropertyRef("slug", extra_index=True)
    created_at: PropertyRef = PropertyRef("createdAt")
    avatar: PropertyRef = PropertyRef("avatar")


@dataclass(frozen=True)
class VercelTeamSchema(CartographyNodeSchema):
    label: str = "VercelTeam"
    properties: VercelTeamNodeProperties = VercelTeamNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
