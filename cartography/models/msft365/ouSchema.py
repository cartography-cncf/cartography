from dataclasses import dataclass, field
from typing import List
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties, CartographyRelSchema

@dataclass(frozen=True)
class Msft365OrganizationalUnitProperties(CartographyNodeProperties):
    id: PropertyRef = field(default=PropertyRef('id', 'The organizational unit id'))
    displayName: PropertyRef = field(default=PropertyRef('displayName', 'The display name of the organizational unit'))
    description: PropertyRef = field(default=PropertyRef('description', 'The description of the organizational unit'))  # Removed optional=True
    lastupdated: PropertyRef = field(default=PropertyRef('lastupdated', 'Timestamp of last update'))
@dataclass(frozen=True)
class Msft365OUToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = field(default=PropertyRef('lastupdated', 'The time when this relationship was last updated'))

@dataclass(frozen=True)
class Msft365OUToUserRelSchema(CartographyRelSchema):
    target_node_label: str = 'Msft365User'
    rel_label: str = 'CONTAINS'
    direction: str = 'OUTGOING'
    properties: Msft365OUToUserRelProperties = field(default=Msft365OUToUserRelProperties())

@dataclass(frozen=True)
class Msft365OUToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = field(default=PropertyRef('lastupdated', 'The time when this relationship was last updated'))

@dataclass(frozen=True)
class Msft365OUToGroupRelSchema(CartographyRelSchema):
    target_node_label: str = 'Msft365Group'
    rel_label: str = 'CONTAINS'
    direction: str = 'OUTGOING'
    properties: Msft365OUToGroupRelProperties = field(default=Msft365OUToGroupRelProperties())

@dataclass(frozen=True)
class Msft365OrganizationalUnitSchema(CartographyNodeSchema):
    label: str = 'Msft365OrganizationalUnit'
    properties: Msft365OrganizationalUnitProperties = field(default=Msft365OrganizationalUnitProperties())
    relationships: List[CartographyRelSchema] = field(
        default_factory=lambda: [
            Msft365OUToUserRelSchema(),
            Msft365OUToGroupRelSchema()
        ]  # Fixed list syntax
    )
