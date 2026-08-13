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
class SnowflakeMaterializedViewNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the materialized view."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The materialized view name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="The fully-qualified name, as DATABASE.SCHEMA.MATERIALIZED_VIEW.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name",
        extra_index=True,
        description="Name of the database that contains the materialized view.",
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name",
        extra_index=True,
        description="Name of the schema that contains the materialized view.",
    )
    is_secure: PropertyRef = PropertyRef(
        "is_secure",
        description=(
            "Whether the materialized view is secure, which hides its definition "
            "and stops the optimizer leaking rows the definition filters out."
        ),
    )
    query: PropertyRef = PropertyRef(
        "query",
        description="The SELECT statement the materialized view keeps precomputed.",
    )
    source_name: PropertyRef = PropertyRef(
        "source_name",
        description="Name of the base table the materialized view is defined over.",
    )
    source_database_name: PropertyRef = PropertyRef(
        "source_database_name",
        description="Database of the base table the materialized view reads.",
    )
    source_schema_name: PropertyRef = PropertyRef(
        "source_schema_name",
        description="Schema of the base table the materialized view reads.",
    )
    row_count: PropertyRef = PropertyRef(
        "row_count",
        description="Number of rows Snowflake reports for the materialized view.",
    )
    size_bytes: PropertyRef = PropertyRef(
        "size_bytes",
        description="Bytes of storage the materialized view occupies.",
    )
    cluster_by: PropertyRef = PropertyRef(
        "cluster_by", description="Clustering key expression, if there is one."
    )
    automatic_clustering: PropertyRef = PropertyRef(
        "automatic_clustering",
        description="Whether Snowflake reclusters the materialized view automatically.",
    )
    invalid: PropertyRef = PropertyRef(
        "invalid",
        description=(
            "Whether the materialized view is suspended and no longer being "
            "maintained, in which case queries fall back to the base table."
        ),
    )
    invalid_reason: PropertyRef = PropertyRef(
        "invalid_reason",
        description="Why Snowflake invalidated the materialized view.",
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the materialized view."
    )
    owner_role_type: PropertyRef = PropertyRef(
        "owner_role_type",
        description="Whether the owner is a ROLE or a DATABASE_ROLE.",
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Materialized view comment."
    )
    refreshed_on: PropertyRef = PropertyRef(
        "refreshed_on", description="When the materialized view was last refreshed."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the materialized view was created."
    )


@dataclass(frozen=True)
class SnowflakeMaterializedViewToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeMaterializedView)
class SnowflakeMaterializedViewToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the materialized view as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeMaterializedViewToAccountRelProperties = (
        SnowflakeMaterializedViewToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeMaterializedViewToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeMaterializedView)
class SnowflakeMaterializedViewToSchemaRel(CartographyRelSchema):
    """A Snowflake schema contains the materialized view."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeMaterializedViewToSchemaRelProperties = (
        SnowflakeMaterializedViewToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeMaterializedViewSchema(CartographyNodeSchema):
    """Represents a Snowflake materialized view: a query whose results are stored and kept fresh."""

    label: str = "SnowflakeMaterializedView"
    properties: SnowflakeMaterializedViewNodeProperties = (
        SnowflakeMaterializedViewNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    # Scoped to the account, not the schema: cleanup has to be able to delete a
    # materialized view whose schema was dropped between syncs.
    sub_resource_relationship: SnowflakeMaterializedViewToAccountRel = (
        SnowflakeMaterializedViewToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeMaterializedViewToSchemaRel()],
    )
