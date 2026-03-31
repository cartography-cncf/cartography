from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class SubImageTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    account_id: PropertyRef = PropertyRef("account_id")
    scan_role_name: PropertyRef = PropertyRef("scan_role_name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SubImageTenantSchema(CartographyNodeSchema):
    label: str = "SubImageTenant"
    properties: SubImageTenantNodeProperties = SubImageTenantNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
