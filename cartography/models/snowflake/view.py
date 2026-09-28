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
class SnowflakeViewNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the view."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The view name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="The fully-qualified view name, as DATABASE.SCHEMA.VIEW.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name",
        extra_index=True,
        description="Name of the database that contains the view.",
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name",
        extra_index=True,
        description="Name of the schema that contains the view.",
    )
    kind: PropertyRef = PropertyRef(
        "kind", description="The view kind reported by Snowflake."
    )
    is_secure: PropertyRef = PropertyRef(
        "is_secure",
        description=(
            "Whether the view is secure. A non-secure view exposes its definition "
            "and lets the optimizer leak rows the definition meant to filter out, "
            "so a view used as a row-level access boundary should be secure."
        ),
    )
    query: PropertyRef = PropertyRef(
        "query",
        description="The SELECT statement that defines the view.",
    )
    column_count: PropertyRef = PropertyRef(
        "column_count",
        description=(
            "Number of columns the view returns. The column list itself is not "
            "stored: one node per column would dwarf the rest of the graph."
        ),
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the view."
    )
    owner_role_type: PropertyRef = PropertyRef(
        "owner_role_type",
        description="Whether the owner is a ROLE or a DATABASE_ROLE.",
    )
    comment: PropertyRef = PropertyRef("comment", description="View comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the view was created."
    )


@dataclass(frozen=True)
class SnowflakeViewToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeView)
class SnowflakeViewToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the view as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeViewToAccountRelProperties = (
        SnowflakeViewToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeViewToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeView)
class SnowflakeViewToSchemaRel(CartographyRelSchema):
    """A Snowflake schema contains the view."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeViewToSchemaRelProperties = (
        SnowflakeViewToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeViewSchema(CartographyNodeSchema):
    """Represents a Snowflake view, a named query over one or more tables."""

    label: str = "SnowflakeView"
    properties: SnowflakeViewNodeProperties = SnowflakeViewNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    # Scoped to the account, not the schema: cleanup has to be able to delete a
    # view whose schema was dropped between syncs.
    sub_resource_relationship: SnowflakeViewToAccountRel = SnowflakeViewToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeViewToSchemaRel()],
    )
