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
class DatabricksGenieSpaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Workspace-scoped identifier for the Databricks Genie space."
    )
    space_id: PropertyRef = PropertyRef(
        "space_id", extra_index=True, description="Databricks Genie space identifier."
    )
    title: PropertyRef = PropertyRef(
        "title", extra_index=True, description="Title of the Genie space."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of the Genie space."
    )
    warehouse_id: PropertyRef = PropertyRef(
        "warehouse_id",
        extra_index=True,
        description="Identifier of the SQL warehouse used by the Genie space.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksGenieSpaceToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksGenieSpace)
class DatabricksGenieSpaceToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains this Genie space resource."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksGenieSpaceToWorkspaceRelProperties = (
        DatabricksGenieSpaceToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksGenieSpaceToWarehouseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksGenieSpace)-[:USES_WAREHOUSE]->(:DatabricksSqlWarehouse)
class DatabricksGenieSpaceToWarehouseRel(CartographyRelSchema):
    """A Databricks Genie space uses a SQL warehouse."""

    target_node_label: str = "DatabricksSqlWarehouse"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("warehouse_scoped_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_WAREHOUSE"
    properties: DatabricksGenieSpaceToWarehouseRelProperties = (
        DatabricksGenieSpaceToWarehouseRelProperties()
    )


@dataclass(frozen=True)
class DatabricksGenieSpaceSchema(CartographyNodeSchema):
    """A Databricks Genie space for natural-language data analysis."""

    label: str = "DatabricksGenieSpace"
    properties: DatabricksGenieSpaceNodeProperties = (
        DatabricksGenieSpaceNodeProperties()
    )
    sub_resource_relationship: DatabricksGenieSpaceToWorkspaceRel = (
        DatabricksGenieSpaceToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksGenieSpaceToWarehouseRel()],
    )
