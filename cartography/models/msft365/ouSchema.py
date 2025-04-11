from dataclasses import dataclass, field
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties, CartographyRelSchema


# ===================================================================
# Node Properties
# ===================================================================

@dataclass(frozen=True)
class Msft365OUProperties(CartographyNodeProperties):
    id: PropertyRef = field(default=PropertyRef('id', 'Organizational Unit ID'))
    displayName: PropertyRef = field(default=PropertyRef('displayName', 'OU Name'))
    description: PropertyRef = field(default=PropertyRef('description', 'OU Description'))
    lastupdated: PropertyRef = field(default=PropertyRef('lastupdated', 'Timestamp of last update'))


# ===================================================================
# Relationship Properties
# ===================================================================

@dataclass(frozen=True)
class Msft365OUTargetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = field(default=PropertyRef('lastupdated', 'Last update timestamp'))


# ===================================================================
# Relationship Schemas
# ===================================================================

@dataclass(frozen=True)
class Msft365OUToUserRelSchema(CartographyRelSchema):
    target_node_label: str = 'Msft365User'
    rel_label: str = 'HAS_USER'
    direction: str = 'OUTGOING'
    properties: Msft365OUTargetRelProperties = field(default=Msft365OUTargetRelProperties())


@dataclass(frozen=True)
class Msft365OUToGroupRelSchema(CartographyRelSchema):
    target_node_label: str = 'Msft365Group'
    rel_label: str = 'HAS_GROUP'
    direction: str = 'OUTGOING'
    properties: Msft365OUTargetRelProperties = field(default=Msft365OUTargetRelProperties())


@dataclass(frozen=True)
class Msft365UserToOrgUnitRelSchema(CartographyRelSchema):
    target_node_label: str = 'Msft365OrganizationalUnit'
    rel_label: str = 'MEMBER_OF_OU'
    direction: str = 'OUTGOING'
    properties: Msft365OUTargetRelProperties = field(default=Msft365OUTargetRelProperties())


# ===================================================================
# Node Schema
# ===================================================================

@dataclass(frozen=True)
class Msft365OrganizationalUnitSchema(CartographyNodeSchema):
    label: str = 'Msft365OrganizationalUnit'
    properties: Msft365OUProperties = field(default=Msft365OUProperties())
    relationships: list[CartographyRelSchema] = field(default_factory=lambda: [
        Msft365OUToUserRelSchema(),
        Msft365OUToGroupRelSchema(),
    ])

    def create_node_merge_statement(self, record: dict, update_tag: str) -> tuple[str, dict]:
        props = ', '.join([f"{key}: ${key}" for key in record.keys()])
        cypher = f"""
        MERGE (n:{self.label} {{id: $id}})
        SET n += {{{props}}},
            n.lastupdated = $update_tag
        """
        params = record.copy()
        params["update_tag"] = update_tag
        return cypher, params
