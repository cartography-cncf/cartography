from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class SantaObservedApplicationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    identifier: PropertyRef = PropertyRef("identifier", extra_index=True)
    source_name: PropertyRef = PropertyRef("source_name")


@dataclass(frozen=True)
class SantaObservedApplicationSchema(CartographyNodeSchema):
    label: str = "SantaObservedApplication"
    scoped_cleanup: bool = False
    properties: SantaObservedApplicationNodeProperties = (
        SantaObservedApplicationNodeProperties()
    )
