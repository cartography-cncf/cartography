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
class SnowflakeTableNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the table."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The table name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="The fully-qualified table name, as DATABASE.SCHEMA.TABLE.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name",
        extra_index=True,
        description="Name of the database that contains the table.",
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name",
        extra_index=True,
        description="Name of the schema that contains the table.",
    )
    kind: PropertyRef = PropertyRef(
        "kind", description="The table kind reported by Snowflake."
    )
    table_type: PropertyRef = PropertyRef(
        "table_type",
        extra_index=True,
        description=(
            "The table flavour: NORMAL, DYNAMIC, EXTERNAL, EVENT, HYBRID, ICEBERG "
            "or IMMUTABLE."
        ),
    )
    row_count: PropertyRef = PropertyRef(
        "row_count", description="Number of rows Snowflake reports for the table."
    )
    size_bytes: PropertyRef = PropertyRef(
        "size_bytes", description="Bytes of storage the table occupies."
    )
    column_count: PropertyRef = PropertyRef(
        "column_count",
        description=(
            "Number of columns in the table. The column list itself is not stored: "
            "one node per column would dwarf the rest of the graph."
        ),
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the table."
    )
    owner_role_type: PropertyRef = PropertyRef(
        "owner_role_type",
        description="Whether the owner is a ROLE or a DATABASE_ROLE.",
    )
    comment: PropertyRef = PropertyRef("comment", description="Table comment.")
    cluster_by: PropertyRef = PropertyRef(
        "cluster_by", description="Clustering key expression, if the table has one."
    )
    change_tracking: PropertyRef = PropertyRef(
        "change_tracking",
        description="Whether change tracking is enabled, which streams require.",
    )
    enable_schema_evolution: PropertyRef = PropertyRef(
        "enable_schema_evolution",
        description=(
            "Whether loading a file may add columns to the table, which lets an "
            "ingestion path widen the table without a DDL change."
        ),
    )
    search_optimization: PropertyRef = PropertyRef(
        "search_optimization",
        description="Whether the search optimization service is enabled on the table.",
    )
    data_retention_time_in_days: PropertyRef = PropertyRef(
        "data_retention_time_in_days",
        description=(
            "Time Travel window in days. A value of 0 disables Time Travel, which "
            "removes the ability to recover rows after an accidental or malicious "
            "change."
        ),
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the table was created."
    )
    dropped_on: PropertyRef = PropertyRef(
        "dropped_on",
        description="When the table was dropped, if it is pending purge.",
    )


@dataclass(frozen=True)
class SnowflakeTableToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeTable)
class SnowflakeTableToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the table as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeTableToAccountRelProperties = (
        SnowflakeTableToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeTableToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeTable)
class SnowflakeTableToSchemaRel(CartographyRelSchema):
    """A Snowflake schema contains the table."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeTableToSchemaRelProperties = (
        SnowflakeTableToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeTableSchema(CartographyNodeSchema):
    """Represents a Snowflake table, where the account's data actually sits."""

    label: str = "SnowflakeTable"
    properties: SnowflakeTableNodeProperties = SnowflakeTableNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    # Scoped to the account, not the schema: cleanup has to be able to delete a
    # table whose schema was dropped between syncs.
    sub_resource_relationship: SnowflakeTableToAccountRel = SnowflakeTableToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeTableToSchemaRel()],
    )
