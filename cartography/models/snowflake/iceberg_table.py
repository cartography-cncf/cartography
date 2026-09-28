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
class SnowflakeIcebergTableNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the Iceberg table."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The Iceberg table name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="The fully-qualified name, as DATABASE.SCHEMA.ICEBERG_TABLE.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name",
        extra_index=True,
        description="Name of the database that contains the Iceberg table.",
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name",
        extra_index=True,
        description="Name of the schema that contains the Iceberg table.",
    )
    external_volume: PropertyRef = PropertyRef(
        "external_volume",
        extra_index=True,
        description=(
            "Name of the external volume holding the table's data and metadata "
            "files, which sit in customer-owned cloud storage."
        ),
    )
    catalog: PropertyRef = PropertyRef(
        "catalog",
        description=(
            "Name of the catalog tracking the table. The literal SNOWFLAKE means "
            "Snowflake itself is the catalog rather than an external integration."
        ),
    )
    catalog_sync: PropertyRef = PropertyRef(
        "catalog_sync",
        description=(
            "Name of the catalog integration the table's metadata is synced out to, "
            "which makes it readable by engines outside Snowflake."
        ),
    )
    catalog_table_name: PropertyRef = PropertyRef(
        "catalog_table_name",
        description="Name of the table as the external catalog knows it.",
    )
    catalog_namespace: PropertyRef = PropertyRef(
        "catalog_namespace",
        description="Namespace of the table in the external catalog.",
    )
    base_location: PropertyRef = PropertyRef(
        "base_location",
        description="Path within the external volume holding the table's files.",
    )
    iceberg_table_type: PropertyRef = PropertyRef(
        "iceberg_table_type",
        description=(
            "Whether Snowflake manages the table or only reads a table an external "
            "catalog manages."
        ),
    )
    storage_serialization_policy: PropertyRef = PropertyRef(
        "storage_serialization_policy",
        description=(
            "How Snowflake encodes the Parquet files, which decides whether other "
            "Iceberg engines can read them."
        ),
    )
    can_write_metadata: PropertyRef = PropertyRef(
        "can_write_metadata",
        description=(
            "Whether Snowflake may write Iceberg metadata for the table, meaning it "
            "needs write access to the external volume rather than read-only."
        ),
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the Iceberg table."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the Iceberg table was created."
    )


@dataclass(frozen=True)
class SnowflakeIcebergTableToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeIcebergTable)
class SnowflakeIcebergTableToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the Iceberg table as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeIcebergTableToAccountRelProperties = (
        SnowflakeIcebergTableToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeIcebergTableToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeIcebergTable)
class SnowflakeIcebergTableToSchemaRel(CartographyRelSchema):
    """A Snowflake schema contains the Iceberg table."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeIcebergTableToSchemaRelProperties = (
        SnowflakeIcebergTableToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeIcebergTableToExternalVolumeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeIcebergTable)-[:STORED_IN]->(:SnowflakeExternalVolume)
class SnowflakeIcebergTableToExternalVolumeRel(CartographyRelSchema):
    """The Iceberg table's files live on this external volume.

    The volume points at customer-owned cloud storage, so anyone with access to
    that storage can read the table's data without going through Snowflake.
    """

    target_node_label: str = "SnowflakeExternalVolume"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("external_volume_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "STORED_IN"
    properties: SnowflakeIcebergTableToExternalVolumeRelProperties = (
        SnowflakeIcebergTableToExternalVolumeRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeIcebergTableToCatalogIntegrationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeIcebergTable)-[:USES_CATALOG]->(:SnowflakeCatalogIntegration)
class SnowflakeIcebergTableToCatalogIntegrationRel(CartographyRelSchema):
    """An external catalog integration, rather than Snowflake, tracks this table.

    Absent when Snowflake is its own catalog, which is the case for tables
    Snowflake manages end to end.
    """

    target_node_label: str = "SnowflakeCatalogIntegration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("catalog_integration_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_CATALOG"
    properties: SnowflakeIcebergTableToCatalogIntegrationRelProperties = (
        SnowflakeIcebergTableToCatalogIntegrationRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeIcebergTableSchema(CartographyNodeSchema):
    """Represents a Snowflake Iceberg table, whose files sit on customer-owned cloud storage."""

    label: str = "SnowflakeIcebergTable"
    properties: SnowflakeIcebergTableNodeProperties = (
        SnowflakeIcebergTableNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    # Scoped to the account, not the schema: cleanup has to be able to delete an
    # Iceberg table whose schema was dropped between syncs.
    sub_resource_relationship: SnowflakeIcebergTableToAccountRel = (
        SnowflakeIcebergTableToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeIcebergTableToSchemaRel(),
            SnowflakeIcebergTableToExternalVolumeRel(),
            SnowflakeIcebergTableToCatalogIntegrationRel(),
        ],
    )
