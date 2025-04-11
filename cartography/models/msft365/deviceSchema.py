# cartography/models/msft365/deviceSchema.py

from dataclasses import dataclass, field
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties, CartographyRelSchema

# ============================================================
# Node Properties
# ============================================================

@dataclass(frozen=True)
class Msft365DeviceProperties(CartographyNodeProperties):
    id: PropertyRef = field(default=PropertyRef('id', 'Device ID'))
    displayName: PropertyRef = field(default=PropertyRef('displayName', 'Device name'))
    operatingSystem: PropertyRef = field(default=PropertyRef('operatingSystem', 'Device OS'))
    deviceOwnership: PropertyRef = field(default=PropertyRef('deviceOwnership', 'Ownership type'))
    lastupdated: PropertyRef = field(default=PropertyRef('lastupdated', 'Timestamp of last update'))

# ============================================================
# Relationship Properties
# ============================================================

@dataclass(frozen=True)
class Msft365DeviceOwnerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = field(default=PropertyRef('lastupdated', 'Last update timestamp'))

# ============================================================
# Relationships
# ============================================================

@dataclass(frozen=True)
class Msft365DeviceOwnerRelSchema(CartographyRelSchema):
    target_node_label: str = 'Msft365User'
    rel_label: str = 'OWNED_BY'
    direction: str = 'OUTGOING'
    properties: Msft365DeviceOwnerRelProperties = field(default=Msft365DeviceOwnerRelProperties())

    def target_node_matcher(self, input: dict) -> dict:
        return {"id": input["ownerId"]}
    
    def create_relationship_statement(self, record: dict, update_tag: str) -> tuple[str, dict]:
        cypher = f"""
        MATCH (source:Msft365Device {{id: $source_id}})
        MATCH (target:{self.target_node_label} {{id: $target_id}})
        MERGE (source)-[r:{self.rel_label}]->(target)
        SET r.lastupdated = $lastupdated
        """
        params = record.copy()
        params["lastupdated"] = update_tag
        return cypher, params

@dataclass(frozen=True)
class Msft365UserToDeviceRelSchema(CartographyRelSchema):
    target_node_label: str = 'Msft365Device'
    rel_label: str = 'OWNS_DEVICE'
    direction: str = 'OUTGOING'
    properties: Msft365DeviceOwnerRelProperties = field(default=Msft365DeviceOwnerRelProperties())
    type: str = "Msft365UserToDevice"

    def target_node_matcher(self, input: dict) -> dict:
        return {"id": input["deviceId"]}

    def create_relationship_statement(self, record: dict, update_tag: str) -> tuple[str, dict]:
        cypher = f"""
        MATCH (source:Msft365User {{id: $source_id}})
        MATCH (target:{self.target_node_label} {{id: $target_id}})
        MERGE (source)-[r:{self.rel_label}]->(target)
        SET r.lastupdated = $lastupdated
        """
        params = record.copy()
        params["lastupdated"] = update_tag
        return cypher, params    


# ============================================================
# Device Node Schema
# ============================================================

@dataclass(frozen=True)
class Msft365DeviceSchema(CartographyNodeSchema):
    label: str = 'Msft365Device'
    properties: Msft365DeviceProperties = field(default=Msft365DeviceProperties())
    relationships: list[CartographyRelSchema] = field(default_factory=lambda: [
        Msft365DeviceOwnerRelSchema(),
        Msft365UserToDeviceRelSchema(),
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
