from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class GSuiteTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Unique GSuite customer ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )

    # Customer/domain identifier - use id as the primary identifier
    customer_id: PropertyRef = PropertyRef(
        "id", description="Alias of the unique GSuite customer ID."
    )


@dataclass(frozen=True)
class GSuiteTenantSchema(CartographyNodeSchema):
    """A GSuite customer account with the canonical Tenant label."""

    label: str = "GSuiteTenant"
    properties: GSuiteTenantNodeProperties = GSuiteTenantNodeProperties()
    sub_resource_relationship: None = None  # Tenant is the root level
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
