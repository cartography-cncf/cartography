from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class AzureTagProperties(CartographyNodeProperties):
    # The ID is a string: "{key}:{value}"
    id: PropertyRef = PropertyRef("id")
    key: PropertyRef = PropertyRef("key")
    value: PropertyRef = PropertyRef("value")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureTagSchema(CartographyNodeSchema):
    label: str = "AzureTag"
    properties: AzureTagProperties = AzureTagProperties()
