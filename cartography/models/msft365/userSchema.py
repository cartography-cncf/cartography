from dataclasses import dataclass, field
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties, CartographyRelSchema

@dataclass(frozen=True)
class Msft365UserProperties(CartographyNodeProperties):
    id: PropertyRef = field(default=PropertyRef('id', 'The user id'))
    displayName: PropertyRef = field(default=PropertyRef('displayName', 'The display name of the user'))
    userPrincipalName: PropertyRef = field(default=PropertyRef('userPrincipalName', 'The user principal name (UPN)'))
    mail: PropertyRef = field(default=PropertyRef('mail', 'The primary email address'))
    jobTitle: PropertyRef = field(default=PropertyRef('jobTitle', 'The job title of the user'))
    department: PropertyRef = field(default=PropertyRef('department', 'The department of the user'))
    lastupdated: PropertyRef = field(default=PropertyRef('lastupdated', 'Timestamp of last update'))

@dataclass(frozen=True)
class Msft365UserToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = field(default=PropertyRef('lastupdated', 'The time when this relationship was updated'))

@dataclass(frozen=True)
class Msft365UserToGroupRelSchema(CartographyRelSchema):
    target_node_label: str = 'Msft365Group'
    rel_label: str = 'MEMBER_OF'
    direction: str = 'OUTGOING'
    properties: Msft365UserToGroupRelProperties = field(default=Msft365UserToGroupRelProperties())

@dataclass(frozen=True)
class Msft365UserSchema(CartographyNodeSchema):
    label: str = 'Msft365User'
    properties: Msft365UserProperties = field(default=Msft365UserProperties())
    relationships: list[CartographyRelSchema] = field(default_factory=lambda: [Msft365UserToGroupRelSchema()])
