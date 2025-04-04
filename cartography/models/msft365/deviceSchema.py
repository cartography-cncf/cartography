from dataclasses import dataclass, field
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties, CartographyRelSchema

@dataclass(frozen=True)
class Msft365DeviceProperties(CartographyNodeProperties):
    id: PropertyRef = field(default=PropertyRef('id', 'Device ID'))
    displayName: PropertyRef = field(default=PropertyRef('displayName', 'Device name'))
    operatingSystem: PropertyRef = field(default=PropertyRef('operatingSystem', 'Device OS'))
    deviceOwnership: PropertyRef = field(default=PropertyRef('deviceOwnership', 'Ownership type'))
    lastupdated: PropertyRef = field(default=PropertyRef('lastupdated', 'Timestamp of last update'))

@dataclass(frozen=True)
class Msft365DeviceOwnerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = field(default=PropertyRef('lastupdated', 'Last update timestamp'))

@dataclass(frozen=True)
class Msft365DeviceOwnerRelSchema(CartographyRelSchema):
    target_node_label: str = 'Msft365User'
    rel_label: str = 'OWNED_BY'
    direction: str = 'OUTGOING'
    properties: Msft365DeviceOwnerRelProperties = field(default=Msft365DeviceOwnerRelProperties())

@dataclass(frozen=True)
class Msft365DeviceSchema(CartographyNodeSchema):
    label: str = 'Msft365Device'
    properties: Msft365DeviceProperties = field(default=Msft365DeviceProperties())
    relationships: list[CartographyRelSchema] = field(default_factory=lambda: [Msft365DeviceOwnerRelSchema()])
