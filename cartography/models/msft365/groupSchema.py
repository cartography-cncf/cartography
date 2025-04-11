from dataclasses import dataclass, field
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema


# ============================================================
# Node Properties
# ============================================================

@dataclass(frozen=True)
class Msft365GroupProperties(CartographyNodeProperties):
    id: PropertyRef = field(default=PropertyRef('id', 'The group id'))
    displayName: PropertyRef = field(default=PropertyRef('displayName', 'The display name'))
    description: PropertyRef = field(default=PropertyRef('description', 'The group description'))
    mail: PropertyRef = field(default=PropertyRef('mail', 'The group email'))
    lastupdated: PropertyRef = field(default=PropertyRef('lastupdated', 'Timestamp of last update'))


# ============================================================
# Node Schema
# ============================================================

@dataclass(frozen=True)
class Msft365GroupSchema(CartographyNodeSchema):
    label: str = 'Msft365Group'
    properties: Msft365GroupProperties = field(default=Msft365GroupProperties())

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
