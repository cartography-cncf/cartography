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
class SnowflakeExternalTableNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the external table."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The external table name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="The fully-qualified name, as DATABASE.SCHEMA.EXTERNAL_TABLE.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name",
        extra_index=True,
        description="Name of the database that contains the external table.",
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name",
        extra_index=True,
        description="Name of the schema that contains the external table.",
    )
    stage: PropertyRef = PropertyRef(
        "stage",
        description="Name of the stage the external table reads its files through.",
    )
    location: PropertyRef = PropertyRef(
        "location",
        extra_index=True,
        description=(
            "Cloud storage prefix the files are read from. The data lives outside "
            "Snowflake, so its access controls are the storage provider's."
        ),
    )
    cloud: PropertyRef = PropertyRef(
        "cloud", description="Cloud provider hosting the underlying files."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Cloud region hosting the underlying files."
    )
    file_format_name: PropertyRef = PropertyRef(
        "file_format_name",
        description="Name of the file format used to parse the files.",
    )
    file_format_type: PropertyRef = PropertyRef(
        "file_format_type",
        description="File format type, for example CSV, JSON or PARQUET.",
    )
    table_format: PropertyRef = PropertyRef(
        "table_format",
        description="Table format layered over the files, for example DELTA.",
    )
    notification_channel: PropertyRef = PropertyRef(
        "notification_channel",
        description=(
            "Cloud messaging channel that triggers automatic metadata refreshes."
        ),
    )
    invalid: PropertyRef = PropertyRef(
        "invalid",
        description=(
            "Whether Snowflake marked the external table invalid, meaning it can no "
            "longer read its files."
        ),
    )
    invalid_reason: PropertyRef = PropertyRef(
        "invalid_reason",
        description="Why Snowflake invalidated the external table.",
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the external table."
    )
    owner_role_type: PropertyRef = PropertyRef(
        "owner_role_type",
        description="Whether the owner is a ROLE or a DATABASE_ROLE.",
    )
    comment: PropertyRef = PropertyRef("comment", description="External table comment.")
    last_refreshed_on: PropertyRef = PropertyRef(
        "last_refreshed_on",
        description="When the external table metadata was last refreshed.",
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the external table was created."
    )


@dataclass(frozen=True)
class SnowflakeExternalTableToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeExternalTable)
class SnowflakeExternalTableToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the external table as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeExternalTableToAccountRelProperties = (
        SnowflakeExternalTableToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeExternalTableToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeExternalTable)
class SnowflakeExternalTableToSchemaRel(CartographyRelSchema):
    """A Snowflake schema contains the external table."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeExternalTableToSchemaRelProperties = (
        SnowflakeExternalTableToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeExternalTableToStageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeExternalTable)-[:READS_FROM]->(:SnowflakeStage)
class SnowflakeExternalTableToStageRel(CartographyRelSchema):
    """The external table reads its files through this stage.

    The stage holds the credential or storage integration, so it is the hop that
    turns a query on the external table into access to cloud storage.
    """

    target_node_label: str = "SnowflakeStage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("stage_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "READS_FROM"
    properties: SnowflakeExternalTableToStageRelProperties = (
        SnowflakeExternalTableToStageRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeExternalTableToFileFormatRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeExternalTable)-[:USES_FILE_FORMAT]->(:SnowflakeFileFormat)
class SnowflakeExternalTableToFileFormatRel(CartographyRelSchema):
    """The external table parses its files with this named file format."""

    target_node_label: str = "SnowflakeFileFormat"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("file_format_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_FILE_FORMAT"
    properties: SnowflakeExternalTableToFileFormatRelProperties = (
        SnowflakeExternalTableToFileFormatRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeExternalTableSchema(CartographyNodeSchema):
    """Represents a Snowflake external table: a table whose files stay in cloud storage."""

    label: str = "SnowflakeExternalTable"
    properties: SnowflakeExternalTableNodeProperties = (
        SnowflakeExternalTableNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    # Scoped to the account, not the schema: cleanup has to be able to delete an
    # external table whose schema was dropped between syncs.
    sub_resource_relationship: SnowflakeExternalTableToAccountRel = (
        SnowflakeExternalTableToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeExternalTableToSchemaRel(),
            SnowflakeExternalTableToStageRel(),
            SnowflakeExternalTableToFileFormatRel(),
        ],
    )
