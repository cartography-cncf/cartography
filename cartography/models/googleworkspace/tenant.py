from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class GoogleWorkspaceTenantNodeProperties(CartographyNodeProperties):
    """
    Google Workspace tenant (domain/customer) node properties
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    domain: PropertyRef = PropertyRef("customerDomain")
    name: PropertyRef = PropertyRef("postalAddress.organizationName")


@dataclass(frozen=True)
class GoogleWorkspaceTenantSchema(CartographyNodeSchema):
    """
    Google Workspace tenant (domain/customer) schema
    """

    label: str = "GoogleWorkspaceTenant"
    properties: GoogleWorkspaceTenantNodeProperties = (
        GoogleWorkspaceTenantNodeProperties()
    )
    sub_resource_relationship: None = None  # Tenant is the root level
