from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.zoom.resource import ZoomAccountResourceRel


@dataclass(frozen=True)
class ZoomClientVersionProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped Dashboard client version string."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID",
        set_in_kwargs=True,
        extra_index=True,
        description="Owning Zoom account ID.",
    )
    client_version: PropertyRef = PropertyRef(
        "client_version",
        extra_index=True,
        description="Dashboard client_version, such as a platform-prefixed build string.",
    )
    total_count: PropertyRef = PropertyRef(
        "total_count",
        description="Dashboard total_count reported for this client version.",
    )


@dataclass(frozen=True)
class ZoomClientVersionSchema(CartographyNodeSchema):
    """An account-wide Dashboard count of one Zoom client version.

    This is an aggregate from the client versions report, not a device or user
    inventory, and it cannot be attributed to individual users.
    """

    label: str = "ZoomClientVersion"
    properties: ZoomClientVersionProperties = ZoomClientVersionProperties()
    sub_resource_relationship: ZoomAccountResourceRel = ZoomAccountResourceRel()
