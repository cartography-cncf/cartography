from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class CircleCIOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    slug: PropertyRef = PropertyRef("slug", extra_index=True)
    vcs_type: PropertyRef = PropertyRef("vcs_type")
    avatar_url: PropertyRef = PropertyRef("avatar_url")


@dataclass(frozen=True)
class CircleCIOrganizationSchema(CartographyNodeSchema):
    label: str = "CircleCIOrganization"
    properties: CircleCIOrganizationNodeProperties = (
        CircleCIOrganizationNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
