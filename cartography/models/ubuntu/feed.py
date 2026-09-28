from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class UbuntuCVEFeedNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Feed identifier.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Name of the feed.")
    url: PropertyRef = PropertyRef("url", description="URL of the Ubuntu Security API.")


@dataclass(frozen=True)
class UbuntuCVEFeedSchema(CartographyNodeSchema):
    """The Ubuntu Security CVE data feed that owns every notice and CVE it publishes."""

    label: str = "UbuntuCVEFeed"
    properties: UbuntuCVEFeedNodeProperties = UbuntuCVEFeedNodeProperties()
    sub_resource_relationship: None = None
    scoped_cleanup: bool = False
