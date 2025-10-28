from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class GSuiteTenantNodeProperties(CartographyNodeProperties):
    """
    GSuite tenant (domain/customer) node properties
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Customer/domain identifier - use id as the primary identifier
    customer_id: PropertyRef = PropertyRef("id")


@dataclass(frozen=True)
class GSuiteTenantSchema(CartographyNodeSchema):
    """
    GSuite tenant (domain/customer) schema
    """

    label: str = "GSuiteTenant"
    properties: GSuiteTenantNodeProperties = GSuiteTenantNodeProperties()
    sub_resource_relationship: None = None  # Tenant is the root level
