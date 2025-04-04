from dataclasses import dataclass, field
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema

@dataclass(frozen=True)
class Msft365GroupProperties(CartographyNodeProperties):
    id: PropertyRef = field(default=PropertyRef('id', 'The group id'))
    displayName: PropertyRef = field(default=PropertyRef('displayName', 'The display name'))
    description: PropertyRef = field(default=PropertyRef('description', 'The group description'))
    mail: PropertyRef = field(default=PropertyRef('mail', 'The group email'))
    lastupdated: PropertyRef = field(default=PropertyRef('lastupdated', 'Timestamp of last update'))

@dataclass(frozen=True)
class Msft365GroupSchema(CartographyNodeSchema):
    label: str = 'Msft365Group'
    properties: Msft365GroupProperties = field(default=Msft365GroupProperties())
