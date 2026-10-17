from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class DebianSecurityTrackerFeedNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Feed identifier, always `debian-security-tracker`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    url: PropertyRef = PropertyRef(
        "url",
        description="URL the tracker data was read from.",
    )
    last_modified: PropertyRef = PropertyRef(
        "last_modified",
        description=(
            "Last-Modified time the tracker server reported for the data. Unset when "
            "the server sent none."
        ),
    )
    fetched_at: PropertyRef = PropertyRef(
        "fetched_at",
        description="When the sync started reading the data.",
    )


@dataclass(frozen=True)
class DebianSecurityTrackerFeedSchema(CartographyNodeSchema):
    """
    The [Debian security tracker](https://security-tracker.debian.org/tracker/)
    JSON export, which owns every entry read from it.
    """

    label: str = "DebianSecurityTrackerFeed"
    properties: DebianSecurityTrackerFeedNodeProperties = (
        DebianSecurityTrackerFeedNodeProperties()
    )
    sub_resource_relationship: None = None
    scoped_cleanup: bool = False
