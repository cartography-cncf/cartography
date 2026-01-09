from dataclasses import dataclass
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class MDETenantProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('name', set_in_kwargs=True)


@dataclass(frozen=True)
class MDETenantSchema(CartographyNodeSchema):
    label: str = 'MDETenant'
    properties: MDETenantProperties = MDETenantProperties()
