from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class ScalewayOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayOrganizationSchema(CartographyNodeSchema):
    label: str = "ScalewayOrganization"
    properties: ScalewayOrganizationNodeProperties = (
        ScalewayOrganizationNodeProperties()
    )
