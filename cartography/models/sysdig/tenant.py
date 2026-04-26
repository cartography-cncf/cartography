from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class SysdigTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    api_url: PropertyRef = PropertyRef("api_url")


@dataclass(frozen=True)
class SysdigTenantSchema(CartographyNodeSchema):
    label: str = "SysdigTenant"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
    properties: SysdigTenantNodeProperties = SysdigTenantNodeProperties()
