from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class GoogleWorkspaceTenantNodeProperties(CartographyNodeProperties):
    """
    Google Workspace tenant (domain/customer) node properties
    """

    id: PropertyRef = PropertyRef(
        "id", description="Unique Google Workspace customer ID."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    domain: PropertyRef = PropertyRef(
        "customerDomain", description="Primary domain of the customer account."
    )
    name: PropertyRef = PropertyRef(
        "postalAddress.organizationName",
        description="Organization name from the customer postal address.",
    )


@dataclass(frozen=True)
class GoogleWorkspaceTenantSchema(CartographyNodeSchema):
    """A Google Workspace customer account with the canonical Tenant label."""

    label: str = "GoogleWorkspaceTenant"
    properties: GoogleWorkspaceTenantNodeProperties = (
        GoogleWorkspaceTenantNodeProperties()
    )
    sub_resource_relationship: None = None  # Tenant is the root level
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
