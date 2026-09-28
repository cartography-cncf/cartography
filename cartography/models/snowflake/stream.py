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
class SnowflakeStreamNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the stream."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The stream name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="The fully-qualified name, as DATABASE.SCHEMA.STREAM.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name",
        extra_index=True,
        description="Name of the database that contains the stream.",
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name",
        extra_index=True,
        description="Name of the schema that contains the stream.",
    )
    source_type: PropertyRef = PropertyRef(
        "source_type",
        description=(
            "Kind of object the stream tracks changes on, for example Table, View "
            "or Stage."
        ),
    )
    source_name: PropertyRef = PropertyRef(
        "source_name",
        extra_index=True,
        description="Name of the object whose changes the stream reads.",
    )
    mode: PropertyRef = PropertyRef(
        "mode",
        description=(
            "Which change rows the stream returns: DEFAULT, APPEND_ONLY or "
            "INSERT_ONLY."
        ),
    )
    stream_type: PropertyRef = PropertyRef(
        "stream_type",
        description="Stream type reported by Snowflake, for example DELTA.",
    )
    is_stale: PropertyRef = PropertyRef(
        "is_stale",
        description=(
            "Whether the stream went stale. A stale stream silently stops delivering "
            "changes, so a pipeline consuming it will miss data until it is "
            "recreated."
        ),
    )
    stale_after: PropertyRef = PropertyRef(
        "stale_after",
        description="When the stream goes stale if it is not consumed before then.",
    )
    invalid_reason: PropertyRef = PropertyRef(
        "invalid_reason", description="Why Snowflake invalidated the stream."
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the stream."
    )
    comment: PropertyRef = PropertyRef("comment", description="Stream comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the stream was created."
    )


@dataclass(frozen=True)
class SnowflakeStreamToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeStream)
class SnowflakeStreamToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the stream as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeStreamToAccountRelProperties = (
        SnowflakeStreamToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeStreamToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeStream)
class SnowflakeStreamToSchemaRel(CartographyRelSchema):
    """A Snowflake schema contains the stream."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeStreamToSchemaRelProperties = (
        SnowflakeStreamToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeStreamToTableRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeStream)-[:READS_FROM]->(:SnowflakeTable)
class SnowflakeStreamToTableRel(CartographyRelSchema):
    """The stream delivers the change rows of this table.

    Anything granted SELECT on the stream can therefore read the table's changed
    rows without holding a privilege on the table itself.
    """

    target_node_label: str = "SnowflakeTable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("source_table_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "READS_FROM"
    properties: SnowflakeStreamToTableRelProperties = (
        SnowflakeStreamToTableRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeStreamSchema(CartographyNodeSchema):
    """Represents a Snowflake stream, a change-data feed over a table, view or stage."""

    label: str = "SnowflakeStream"
    properties: SnowflakeStreamNodeProperties = SnowflakeStreamNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    # Scoped to the account, not the schema: cleanup has to be able to delete a
    # stream whose schema was dropped between syncs.
    sub_resource_relationship: SnowflakeStreamToAccountRel = (
        SnowflakeStreamToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeStreamToSchemaRel(),
            SnowflakeStreamToTableRel(),
        ],
    )
