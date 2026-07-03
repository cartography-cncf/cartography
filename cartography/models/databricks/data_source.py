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
class DatabricksDataSourceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    data_source_id: PropertyRef = PropertyRef("data_source_id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    type: PropertyRef = PropertyRef("type")
    warehouse_id: PropertyRef = PropertyRef("warehouse_id", extra_index=True)
    syntax: PropertyRef = PropertyRef("syntax")
    paused: PropertyRef = PropertyRef("paused")
    view_only: PropertyRef = PropertyRef("view_only")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksDataSourceToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksDataSource)
class DatabricksDataSourceToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksDataSourceToWorkspaceRelProperties = (
        DatabricksDataSourceToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksDataSourceToWarehouseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksDataSource)-[:BACKED_BY]->(:DatabricksSqlWarehouse)
class DatabricksDataSourceToWarehouseRel(CartographyRelSchema):
    target_node_label: str = "DatabricksSqlWarehouse"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("warehouse_scoped_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BACKED_BY"
    properties: DatabricksDataSourceToWarehouseRelProperties = (
        DatabricksDataSourceToWarehouseRelProperties()
    )


@dataclass(frozen=True)
class DatabricksDataSourceSchema(CartographyNodeSchema):
    label: str = "DatabricksDataSource"
    properties: DatabricksDataSourceNodeProperties = (
        DatabricksDataSourceNodeProperties()
    )
    sub_resource_relationship: DatabricksDataSourceToWorkspaceRel = (
        DatabricksDataSourceToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksDataSourceToWarehouseRel()],
    )
