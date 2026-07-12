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
    id: PropertyRef = PropertyRef("id")
    endpoint_id: PropertyRef = PropertyRef("endpoint_id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    endpoint_type: PropertyRef = PropertyRef("endpoint_type")
    state: PropertyRef = PropertyRef("state")
    num_indexes: PropertyRef = PropertyRef("num_indexes")
    creator: PropertyRef = PropertyRef("creator", extra_index=True)
    created_at: PropertyRef = PropertyRef("created_at")
    last_updated_at: PropertyRef = PropertyRef("last_updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksVSEndpointToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksVectorSearchEndpoint)
class DatabricksVSEndpointToWorkspaceRel(CartographyRelSchema):
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
    label: str = "DatabricksVectorSearchEndpoint"
    properties: DatabricksVectorSearchEndpointNodeProperties = (
        DatabricksVectorSearchEndpointNodeProperties()
    )
    sub_resource_relationship: DatabricksVSEndpointToWorkspaceRel = (
        DatabricksVSEndpointToWorkspaceRel()
    )


@dataclass(frozen=True)
class DatabricksVectorSearchIndexNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    endpoint_name: PropertyRef = PropertyRef("endpoint_name", extra_index=True)
    index_type: PropertyRef = PropertyRef("index_type")
    primary_key: PropertyRef = PropertyRef("primary_key")
    source_table: PropertyRef = PropertyRef("source_table", extra_index=True)
    creator: PropertyRef = PropertyRef("creator", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksVSIndexToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksVectorSearchIndex)
class DatabricksVSIndexToWorkspaceRel(CartographyRelSchema):
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
