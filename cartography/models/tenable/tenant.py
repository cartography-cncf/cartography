from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class TenableTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Configured Tenable tenant ID or normalized base URL."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class TenableTenantSchema(CartographyNodeSchema):
    """A Tenable tenant that scopes imported resources."""

    label: str = "TenableTenant"
    properties: TenableTenantNodeProperties = TenableTenantNodeProperties()
