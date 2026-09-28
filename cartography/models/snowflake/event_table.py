from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeEventTableNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the event table."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The event table name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="The fully-qualified name, as DATABASE.SCHEMA.EVENT_TABLE.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name",
        extra_index=True,
        description="Name of the database that contains the event table.",
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name",
        extra_index=True,
        description="Name of the schema that contains the event table.",
    )
    row_count: PropertyRef = PropertyRef(
        "row_count",
        description="Number of event rows Snowflake reports for the table.",
    )
    size_bytes: PropertyRef = PropertyRef(
        "size_bytes", description="Bytes of storage the event table occupies."
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the event table."
    )
    comment: PropertyRef = PropertyRef("comment", description="Event table comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the event table was created."
    )


@dataclass(frozen=True)
class SnowflakeEventTableToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeEventTable)
class SnowflakeEventTableToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the event table as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeEventTableToAccountRelProperties = (
        SnowflakeEventTableToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeEventTableToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeEventTable)
class SnowflakeEventTableToSchemaRel(CartographyRelSchema):
    """A Snowflake schema contains the event table."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeEventTableToSchemaRelProperties = (
        SnowflakeEventTableToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeEventTableSchema(CartographyNodeSchema):
    """Represents a Snowflake event table, the destination for logs, traces and metrics."""

    label: str = "SnowflakeEventTable"
    properties: SnowflakeEventTableNodeProperties = SnowflakeEventTableNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    # Scoped to the account, not the schema: cleanup has to be able to delete an
    # event table whose schema was dropped between syncs.
    sub_resource_relationship: SnowflakeEventTableToAccountRel = (
        SnowflakeEventTableToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeEventTableToSchemaRel()],
    )
