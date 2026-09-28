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
class SnowflakeCortexSearchServiceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the Cortex Search service."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Cortex Search service name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        description="Fully-qualified database.schema.service name.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name", description="Database containing the service."
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name", description="Schema containing the service."
    )
    target_lag: PropertyRef = PropertyRef(
        "target_lag",
        description="How stale the search index is allowed to be against its source.",
    )
    warehouse: PropertyRef = PropertyRef(
        "warehouse",
        description="Name of the virtual warehouse that refreshes the search index.",
    )
    source: PropertyRef = PropertyRef(
        "source",
        description="Table, view or query the service indexes its documents from.",
    )
    embedding_model: PropertyRef = PropertyRef(
        "embedding_model",
        description="Model used to embed the indexed text for semantic retrieval.",
    )
    attribute_columns: PropertyRef = PropertyRef(
        "attribute_columns",
        description="Source columns exposed as filterable attributes on search results.",
    )
    search_column: PropertyRef = PropertyRef(
        "search_column", description="Source column whose text is indexed and searched."
    )
    service_query_url: PropertyRef = PropertyRef(
        "service_query_url",
        description="Endpoint applications call to query the service.",
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Cortex Search service comment."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the service was created."
    )


@dataclass(frozen=True)
class SnowflakeCortexSearchServiceToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeCortexSearchService)
class SnowflakeCortexSearchServiceToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the Cortex Search service as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeCortexSearchServiceToAccountRelProperties = (
        SnowflakeCortexSearchServiceToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeCortexSearchServiceToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeCortexSearchService)
class SnowflakeCortexSearchServiceToSchemaRel(CartographyRelSchema):
    """A Snowflake schema holds the Cortex Search service in its namespace."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeCortexSearchServiceToSchemaRelProperties = (
        SnowflakeCortexSearchServiceToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeCortexSearchServiceToWarehouseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeCortexSearchService)-[:USES_WAREHOUSE]->(:SnowflakeWarehouse)
class SnowflakeCortexSearchServiceToWarehouseRel(CartographyRelSchema):
    """A Snowflake Cortex Search service refreshes its index on this virtual warehouse."""

    target_node_label: str = "SnowflakeWarehouse"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("warehouse_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_WAREHOUSE"
    properties: SnowflakeCortexSearchServiceToWarehouseRelProperties = (
        SnowflakeCortexSearchServiceToWarehouseRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeCortexSearchServiceToTableRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeCortexSearchService)-[:READS_FROM]->(:SnowflakeTable)
class SnowflakeCortexSearchServiceToTableRel(CartographyRelSchema):
    """A Snowflake Cortex Search service indexes the contents of this table.

    Copying source text into a searchable index moves the data out from behind the
    table's own access controls, so knowing which table feeds a service is what
    makes that exposure visible.
    """

    target_node_label: str = "SnowflakeTable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("source_table_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "READS_FROM"
    properties: SnowflakeCortexSearchServiceToTableRelProperties = (
        SnowflakeCortexSearchServiceToTableRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeCortexSearchServiceSchema(CartographyNodeSchema):
    """Represents a Snowflake Cortex Search service: a managed semantic search index built over account data."""

    label: str = "SnowflakeCortexSearchService"
    properties: SnowflakeCortexSearchServiceNodeProperties = (
        SnowflakeCortexSearchServiceNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakeCortexSearchServiceToAccountRel = (
        SnowflakeCortexSearchServiceToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeCortexSearchServiceToSchemaRel(),
            SnowflakeCortexSearchServiceToWarehouseRel(),
            SnowflakeCortexSearchServiceToTableRel(),
        ],
    )
