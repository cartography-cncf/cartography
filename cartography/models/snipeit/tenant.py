from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class SnipeitTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class SnipeitTenantSchema(CartographyNodeSchema):
    label: str = 'SnipeitTenant'  # The label of the node
    properties: SnipeitTenantNodeProperties = SnipeitTenantNodeProperties()  # An object representing all properties
