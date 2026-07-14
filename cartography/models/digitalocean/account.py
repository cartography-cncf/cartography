from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class DOAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="DigitalOcean account UUID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    uuid: PropertyRef = PropertyRef(
        "uuid",
        description="DigitalOcean account UUID.",
    )
    droplet_limit: PropertyRef = PropertyRef(
        "droplet_limit",
        description="Maximum number of Droplets allowed.",
    )
    floating_ip_limit: PropertyRef = PropertyRef(
        "floating_ip_limit",
        description="Maximum number of floating IPs allowed.",
    )
    status: PropertyRef = PropertyRef("status", description="Account status.")


@dataclass(frozen=True)
class DOAccountSchema(CartographyNodeSchema):
    """A DigitalOcean account."""

    label: str = "DOAccount"
    properties: DOAccountNodeProperties = DOAccountNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
