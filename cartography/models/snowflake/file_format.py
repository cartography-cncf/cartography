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
class SnowflakeFileFormatNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the file format."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The file format name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="The fully-qualified name, as DATABASE.SCHEMA.FILE_FORMAT.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name",
        extra_index=True,
        description="Name of the database that contains the file format.",
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name",
        extra_index=True,
        description="Name of the schema that contains the file format.",
    )
    format_type: PropertyRef = PropertyRef(
        "format_type",
        extra_index=True,
        description="File type the format parses, for example CSV, JSON or PARQUET.",
    )
    format_options: PropertyRef = PropertyRef(
        "format_options",
        description="The format's parsing options, as reported by Snowflake.",
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the file format."
    )
    owner_role_type: PropertyRef = PropertyRef(
        "owner_role_type",
        description="Whether the owner is a ROLE or a DATABASE_ROLE.",
    )
    comment: PropertyRef = PropertyRef("comment", description="File format comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the file format was created."
    )


@dataclass(frozen=True)
class SnowflakeFileFormatToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeFileFormat)
class SnowflakeFileFormatToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the file format as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeFileFormatToAccountRelProperties = (
        SnowflakeFileFormatToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeFileFormatToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeFileFormat)
class SnowflakeFileFormatToSchemaRel(CartographyRelSchema):
    """A Snowflake schema contains the file format."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeFileFormatToSchemaRelProperties = (
        SnowflakeFileFormatToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeFileFormatSchema(CartographyNodeSchema):
    """Represents a Snowflake named file format, the reusable parsing rules for staged files."""

    label: str = "SnowflakeFileFormat"
    properties: SnowflakeFileFormatNodeProperties = SnowflakeFileFormatNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    # Scoped to the account, not the schema: cleanup has to be able to delete a
    # file format whose schema was dropped between syncs.
    sub_resource_relationship: SnowflakeFileFormatToAccountRel = (
        SnowflakeFileFormatToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeFileFormatToSchemaRel()],
    )
