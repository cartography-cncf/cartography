from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class CVEMetadataFeedNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "FEED_ID", description="CVE metadata feed identifier."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    source_nvd: PropertyRef = PropertyRef(
        "source_nvd",
        description="Whether NVD enrichment was enabled for the sync.",
    )
    source_epss: PropertyRef = PropertyRef(
        "source_epss",
        description="Whether EPSS enrichment was enabled for the sync.",
    )


@dataclass(frozen=True)
class CVEMetadataFeedSchema(CartographyNodeSchema):
    """The enrichment feed used to manage CVE metadata lifecycle."""

    label: str = "CVEMetadataFeed"
    properties: CVEMetadataFeedNodeProperties = CVEMetadataFeedNodeProperties()
