from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class KandjiTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Kandji tenant ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class KandjiTenantSchema(CartographyNodeSchema):
    """A Kandji tenant containing managed devices."""

    label: str = "KandjiTenant"  # The label of the node
    properties: KandjiTenantNodeProperties = (
        KandjiTenantNodeProperties()
    )  # An object representing all properties
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
