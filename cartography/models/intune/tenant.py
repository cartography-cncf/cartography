from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class IntuneTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    display_name: PropertyRef = PropertyRef("display_name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class IntuneTenantSchema(CartographyNodeSchema):
    label: str = "AzureTenant"
    properties: IntuneTenantNodeProperties = IntuneTenantNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["IntuneTenant", "Tenant"])
