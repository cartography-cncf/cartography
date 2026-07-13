from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class NullifyTenantNodeProperties(CartographyNodeProperties):
    # The Nullify tenant slug (e.g. "acme" for https://api.acme.nullify.ai).
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)


@dataclass(frozen=True)
class NullifyTenantSchema(CartographyNodeSchema):
    label: str = "NullifyTenant"
    properties: NullifyTenantNodeProperties = NullifyTenantNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
