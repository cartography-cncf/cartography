from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DatabricksVectorSearchEndpointNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Workspace-scoped identifier for the vector search endpoint.",
    )
    endpoint_id: PropertyRef = PropertyRef(
        "endpoint_id",
        extra_index=True,
        description="Databricks vector search endpoint identifier.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the vector search endpoint."
    )
    endpoint_type: PropertyRef = PropertyRef(
        "endpoint_type", description="Type of the vector search endpoint."
    )
    state: PropertyRef = PropertyRef(
        "state", description="Current state of the vector search endpoint."
    )
    num_indexes: PropertyRef = PropertyRef(
        "num_indexes", description="Number of indexes on the endpoint."
    )
    creator: PropertyRef = PropertyRef(
        "creator", extra_index=True, description="Creator of the endpoint."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the endpoint was created."
    )
    last_updated_at: PropertyRef = PropertyRef(
        "last_updated_at", description="Timestamp when the endpoint was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksVSEndpointToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksVectorSearchEndpoint)
class DatabricksVSEndpointToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains this vector search endpoint resource."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksVSEndpointToWorkspaceRelProperties = (
        DatabricksVSEndpointToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksVectorSearchEndpointSchema(CartographyNodeSchema):
    """A Databricks vector search endpoint that hosts indexes."""

    label: str = "DatabricksVectorSearchEndpoint"
    properties: DatabricksVectorSearchEndpointNodeProperties = (
        DatabricksVectorSearchEndpointNodeProperties()
    )
    sub_resource_relationship: DatabricksVSEndpointToWorkspaceRel = (
        DatabricksVSEndpointToWorkspaceRel()
    )


@dataclass(frozen=True)
class DatabricksVectorSearchIndexNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Workspace-scoped identifier for the vector search index."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the vector search index."
    )
    endpoint_name: PropertyRef = PropertyRef(
        "endpoint_name",
        extra_index=True,
        description="Name of the endpoint that hosts the index.",
    )
    index_type: PropertyRef = PropertyRef(
        "index_type", description="Type of the vector search index."
    )
    primary_key: PropertyRef = PropertyRef(
        "primary_key", description="Primary key column of the index."
    )
    source_table: PropertyRef = PropertyRef(
        "source_table",
        extra_index=True,
        description="Fully qualified source table name.",
    )
    creator: PropertyRef = PropertyRef(
        "creator", extra_index=True, description="Creator of the index."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksVSIndexToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksVectorSearchIndex)
class DatabricksVSIndexToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains this vector search index resource."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksVSIndexToWorkspaceRelProperties = (
        DatabricksVSIndexToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksVSIndexToEndpointRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksVectorSearchIndex)-[:USES_ENDPOINT]->(:DatabricksVectorSearchEndpoint)
class DatabricksVSIndexToEndpointRel(CartographyRelSchema):
    """A Databricks vector search index uses an endpoint."""

    target_node_label: str = "DatabricksVectorSearchEndpoint"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("endpoint_id_scoped")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_ENDPOINT"
    properties: DatabricksVSIndexToEndpointRelProperties = (
        DatabricksVSIndexToEndpointRelProperties()
    )


@dataclass(frozen=True)
class DatabricksVSIndexToTableRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksVectorSearchIndex)-[:SOURCED_FROM]->(:DatabricksTable)
class DatabricksVSIndexToTableRel(CartographyRelSchema):
    """A Databricks vector search index is sourced from a table."""

    target_node_label: str = "DatabricksTable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("source_table_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SOURCED_FROM"
    properties: DatabricksVSIndexToTableRelProperties = (
        DatabricksVSIndexToTableRelProperties()
    )


@dataclass(frozen=True)
class DatabricksVectorSearchIndexSchema(CartographyNodeSchema):
    """A Databricks vector search index."""

    label: str = "DatabricksVectorSearchIndex"
    properties: DatabricksVectorSearchIndexNodeProperties = (
        DatabricksVectorSearchIndexNodeProperties()
    )
    sub_resource_relationship: DatabricksVSIndexToWorkspaceRel = (
        DatabricksVSIndexToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DatabricksVSIndexToEndpointRel(),
            DatabricksVSIndexToTableRel(),
        ],
    )
