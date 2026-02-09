from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class PagerDutyVendorProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type")
    summary: PropertyRef = PropertyRef("summary")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    website_url: PropertyRef = PropertyRef("website_url")
    logo_url: PropertyRef = PropertyRef("logo_url")
    thumbnail_url: PropertyRef = PropertyRef("thumbnail_url")
    description: PropertyRef = PropertyRef("description")
    integration_guide_url: PropertyRef = PropertyRef("integration_guide_url")


@dataclass(frozen=True)
class PagerDutyVendorSchema(CartographyNodeSchema):
    label: str = "PagerDutyVendor"
    properties: PagerDutyVendorProperties = PagerDutyVendorProperties()
    scoped_cleanup: bool = False
