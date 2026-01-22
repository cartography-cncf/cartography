from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class AirbyteOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("organizationId")
    name: PropertyRef = PropertyRef("organizationName")
    email: PropertyRef = PropertyRef("email")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AirbyteOrganizationSchema(CartographyNodeSchema):
    label: str = "AirbyteOrganization"
    properties: AirbyteOrganizationNodeProperties = AirbyteOrganizationNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
