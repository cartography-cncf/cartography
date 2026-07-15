from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class SubImageTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="SubImage tenant ID.")
    account_id: PropertyRef = PropertyRef(
        "account_id",
        description="SubImage account ID.",
    )
    scan_role_name: PropertyRef = PropertyRef(
        "scan_role_name",
        description="IAM role name used for scanning.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class SubImageTenantSchema(CartographyNodeSchema):
    """A SubImage tenant containing configured resources."""

    label: str = "SubImageTenant"
    properties: SubImageTenantNodeProperties = SubImageTenantNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
