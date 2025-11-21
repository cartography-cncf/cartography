from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class KonnectOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")


@dataclass(frozen=True)
class KonnectOrganizationSchema(CartographyNodeSchema):
    label: str = "KonnectOrganization"
    properties: KonnectOrganizationNodeProperties = KonnectOrganizationNodeProperties()
