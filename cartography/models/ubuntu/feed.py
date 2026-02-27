from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class UbuntuCVEFeedNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    url: PropertyRef = PropertyRef("url")


@dataclass(frozen=True)
class UbuntuCVEFeedSchema(CartographyNodeSchema):
    label: str = "UbuntuCVEFeed"
    properties: UbuntuCVEFeedNodeProperties = UbuntuCVEFeedNodeProperties()
    sub_resource_relationship: None = None
    scoped_cleanup: bool = False
