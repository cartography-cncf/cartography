from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class CVEMetadataFeedNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("FEED_ID")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    source_nvd: PropertyRef = PropertyRef("source_nvd")
    source_epss: PropertyRef = PropertyRef("source_epss")


@dataclass(frozen=True)
class CVEMetadataFeedSchema(CartographyNodeSchema):
    label: str = "CVEMetadataFeed"
    properties: CVEMetadataFeedNodeProperties = CVEMetadataFeedNodeProperties()
