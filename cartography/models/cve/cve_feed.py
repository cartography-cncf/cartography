from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class CVEFeedNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "FEED_ID",
        description="Unique identifier for the CVE feed.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )
    format: PropertyRef = PropertyRef(
        "format",
        description="Data format published by the feed.",
    )
    version: PropertyRef = PropertyRef(
        "version",
        description="Version of the feed data format.",
    )
    timestamp: PropertyRef = PropertyRef(
        "timestamp",
        description="Timestamp reported by the feed.",
    )


@dataclass(frozen=True)
class CVEFeedSchema(CartographyNodeSchema):
    """A source feed from which Cartography imports CVE records."""

    label: str = "CVEFeed"
    properties: CVEFeedNodeProperties = CVEFeedNodeProperties()
