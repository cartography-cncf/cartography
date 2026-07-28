from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SupabasePoolerNodeProperties(CartographyNodeProperties):
    # Synthesised as "<project ref>/<identifier>".
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    identifier: PropertyRef = PropertyRef("identifier")
    database_type: PropertyRef = PropertyRef("database_type")
    # Supavisor is a second reachable endpoint onto the same Postgres database, so
    # its host, port and auth mode matter for network exposure. The
    # `connection_string` field the API also returns is dropped: it embeds
    # credentials.
    db_host: PropertyRef = PropertyRef("db_host", extra_index=True)
    db_port: PropertyRef = PropertyRef("db_port")
    db_name: PropertyRef = PropertyRef("db_name")
    db_user: PropertyRef = PropertyRef("db_user")
    pool_mode: PropertyRef = PropertyRef("pool_mode")
    is_using_scram_auth: PropertyRef = PropertyRef("is_using_scram_auth")
    default_pool_size: PropertyRef = PropertyRef("default_pool_size")
    max_client_conn: PropertyRef = PropertyRef("max_client_conn")


@dataclass(frozen=True)
class SupabasePoolerToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SupabaseProject)-[:RESOURCE]->(:SupabasePooler)
class SupabasePoolerToProjectRel(CartographyRelSchema):
    target_node_label: str = "SupabaseProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_REF", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SupabasePoolerToProjectRelProperties = (
        SupabasePoolerToProjectRelProperties()
    )


@dataclass(frozen=True)
class SupabasePoolerToDatabaseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SupabasePooler)-[:CONNECTS_TO]->(:SupabaseDatabase)
class SupabasePoolerToDatabaseRel(CartographyRelSchema):
    target_node_label: str = "SupabaseDatabase"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("database_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTS_TO"
    properties: SupabasePoolerToDatabaseRelProperties = (
        SupabasePoolerToDatabaseRelProperties()
    )


@dataclass(frozen=True)
class SupabasePoolerSchema(CartographyNodeSchema):
    label: str = "SupabasePooler"
    properties: SupabasePoolerNodeProperties = SupabasePoolerNodeProperties()
    sub_resource_relationship: SupabasePoolerToProjectRel = SupabasePoolerToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SupabasePoolerToDatabaseRel(),
        ],
    )
