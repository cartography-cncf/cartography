from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class DOAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    uuid: PropertyRef = PropertyRef("uuid")
    droplet_limit: PropertyRef = PropertyRef("droplet_limit")
    floating_ip_limit: PropertyRef = PropertyRef("floating_ip_limit")
    status: PropertyRef = PropertyRef("status")


@dataclass(frozen=True)
class DOAccountSchema(CartographyNodeSchema):
    label: str = "DOAccount"
    properties: DOAccountNodeProperties = DOAccountNodeProperties()
