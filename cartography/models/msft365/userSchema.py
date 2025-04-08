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

    def target_node_matcher(self) -> str:
        return "MATCH (g:Msft365Group {id: $TargetId})"

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

@dataclass(frozen=True)
class Msft365UserSchema(CartographyNodeSchema):
    label: str = 'Msft365User'
    properties: Msft365UserProperties = field(default=Msft365UserProperties())
    relationships: list[CartographyRelSchema] = field(default_factory=lambda: [Msft365UserToGroupRelSchema()])

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