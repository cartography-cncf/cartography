from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class AirbyteOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("organizationId")
    name: PropertyRef = PropertyRef("organizationName")
    email: PropertyRef = PropertyRef("email")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AirbyteOrganizationSchema(CartographyNodeSchema):
    label: str = "AirbyteOrganization"
    properties: AirbyteOrganizationNodeProperties = AirbyteOrganizationNodeProperties()
