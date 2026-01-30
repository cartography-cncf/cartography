from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class AzureTenantProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureTenantSchema(CartographyNodeSchema):
    label: str = "AzureTenant"
    properties: AzureTenantProperties = AzureTenantProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
