from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class DopplerWorkplaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    billing_email: PropertyRef = PropertyRef("billing_email")
    security_email: PropertyRef = PropertyRef("security_email")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DopplerWorkplaceSchema(CartographyNodeSchema):
    label: str = "DopplerWorkplace"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["Tenant"]
    )  # Tenant label is used for ontology mapping
    properties: DopplerWorkplaceNodeProperties = DopplerWorkplaceNodeProperties()
