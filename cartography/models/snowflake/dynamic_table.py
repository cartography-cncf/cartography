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
class SnowflakeDynamicTableNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the dynamic table."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The dynamic table name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="The fully-qualified name, as DATABASE.SCHEMA.DYNAMIC_TABLE.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name",
        extra_index=True,
        description="Name of the database that contains the dynamic table.",
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name",
        extra_index=True,
        description="Name of the schema that contains the dynamic table.",
    )
    warehouse: PropertyRef = PropertyRef(
        "warehouse",
        extra_index=True,
        description="Name of the warehouse that runs the refresh.",
    )
    target_lag: PropertyRef = PropertyRef(
        "target_lag",
        description="How far behind its sources the dynamic table is allowed to fall.",
    )
    refresh_mode: PropertyRef = PropertyRef(
        "refresh_mode",
        description="Whether refreshes are INCREMENTAL or FULL.",
    )
    scheduling_state: PropertyRef = PropertyRef(
        "scheduling_state",
        description=(
            "Whether refreshes are RUNNING or SUSPENDED. A suspended dynamic table "
            "keeps serving stale data without failing queries."
        ),
    )
    query: PropertyRef = PropertyRef(
        "query", description="The SELECT statement the dynamic table materializes."
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the dynamic table."
    )
    comment: PropertyRef = PropertyRef("comment", description="Dynamic table comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the dynamic table was created."
    )


@dataclass(frozen=True)
class SnowflakeDynamicTableToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeDynamicTable)
class SnowflakeDynamicTableToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the dynamic table as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeDynamicTableToAccountRelProperties = (
        SnowflakeDynamicTableToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeDynamicTableToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeDynamicTable)
class SnowflakeDynamicTableToSchemaRel(CartographyRelSchema):
    """A Snowflake schema contains the dynamic table."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeDynamicTableToSchemaRelProperties = (
        SnowflakeDynamicTableToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeDynamicTableToWarehouseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeDynamicTable)-[:USES_WAREHOUSE]->(:SnowflakeWarehouse)
class SnowflakeDynamicTableToWarehouseRel(CartographyRelSchema):
    """The dynamic table runs its refreshes on this warehouse.

    The refresh executes with the dynamic table owner's privileges, so the
    warehouse is where that owner's compute is spent.
    """

    target_node_label: str = "SnowflakeWarehouse"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("warehouse_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_WAREHOUSE"
    properties: SnowflakeDynamicTableToWarehouseRelProperties = (
        SnowflakeDynamicTableToWarehouseRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeDynamicTableSchema(CartographyNodeSchema):
    """Represents a Snowflake dynamic table: a declarative pipeline Snowflake refreshes on a lag target."""

    label: str = "SnowflakeDynamicTable"
    properties: SnowflakeDynamicTableNodeProperties = (
        SnowflakeDynamicTableNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    # Scoped to the account, not the schema: cleanup has to be able to delete a
    # dynamic table whose schema was dropped between syncs.
    sub_resource_relationship: SnowflakeDynamicTableToAccountRel = (
        SnowflakeDynamicTableToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeDynamicTableToSchemaRel(),
            SnowflakeDynamicTableToWarehouseRel(),
        ],
    )
