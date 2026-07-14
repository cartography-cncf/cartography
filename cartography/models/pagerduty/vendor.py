from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class PagerDutyVendorProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Vendor ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    type: PropertyRef = PropertyRef(
        "type", description="PagerDuty object type for the vendor."
    )
    summary: PropertyRef = PropertyRef(
        "summary", description="Short summary of the vendor."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Vendor name."
    )
    website_url: PropertyRef = PropertyRef(
        "website_url", description="URL of the vendor's website."
    )
    logo_url: PropertyRef = PropertyRef(
        "logo_url", description="URL of the vendor's logo."
    )
    thumbnail_url: PropertyRef = PropertyRef(
        "thumbnail_url", description="URL of the vendor's thumbnail image."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Vendor description."
    )
    integration_guide_url: PropertyRef = PropertyRef(
        "integration_guide_url", description="URL of the vendor's integration guide."
    )


@dataclass(frozen=True)
class PagerDutyVendorSchema(CartographyNodeSchema):
    """A vendor that provides PagerDuty integrations."""

    label: str = "PagerDutyVendor"
    properties: PagerDutyVendorProperties = PagerDutyVendorProperties()
    scoped_cleanup: bool = False
