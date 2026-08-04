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
class DatabricksDashboardNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Workspace-scoped identifier for the Databricks dashboard."
    )
    dashboard_id: PropertyRef = PropertyRef(
        "dashboard_id", extra_index=True, description="Databricks dashboard identifier."
    )
    display_name: PropertyRef = PropertyRef(
        "display_name", extra_index=True, description="Display name of the dashboard."
    )
    # LAKEVIEW (current) vs LEGACY (redash-based /preview/sql/dashboards).
    dashboard_type: PropertyRef = PropertyRef(
        "dashboard_type",
        description="Dashboard generation, such as Lakeview or legacy.",
    )
    warehouse_id: PropertyRef = PropertyRef(
        "warehouse_id",
        extra_index=True,
        description="Identifier of the SQL warehouse used by the dashboard.",
    )
    owner_user_name: PropertyRef = PropertyRef(
        "owner_user_name",
        extra_index=True,
        description="User name of the dashboard owner.",
    )
    lifecycle_state: PropertyRef = PropertyRef(
        "lifecycle_state", description="Lifecycle state of the dashboard."
    )
    parent_path: PropertyRef = PropertyRef(
        "parent_path", description="Workspace path of the dashboard's parent folder."
    )
    path: PropertyRef = PropertyRef(
        "path", description="Workspace path of the dashboard."
    )
    create_time: PropertyRef = PropertyRef(
        "create_time", description="Timestamp when the dashboard was created."
    )
    update_time: PropertyRef = PropertyRef(
        "update_time", description="Timestamp when the dashboard was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksDashboardToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksDashboard)
class DatabricksDashboardToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains this dashboard resource."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksDashboardToWorkspaceRelProperties = (
        DatabricksDashboardToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksDashboardToWarehouseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksDashboard)-[:USES_WAREHOUSE]->(:DatabricksSqlWarehouse)
class DatabricksDashboardToWarehouseRel(CartographyRelSchema):
    """A Databricks dashboard uses a SQL warehouse."""

    target_node_label: str = "DatabricksSqlWarehouse"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("warehouse_scoped_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_WAREHOUSE"
    properties: DatabricksDashboardToWarehouseRelProperties = (
        DatabricksDashboardToWarehouseRelProperties()
    )


@dataclass(frozen=True)
class DatabricksDashboardSchema(CartographyNodeSchema):
    """A Databricks dashboard in a workspace."""

    label: str = "DatabricksDashboard"
    properties: DatabricksDashboardNodeProperties = DatabricksDashboardNodeProperties()
    sub_resource_relationship: DatabricksDashboardToWorkspaceRel = (
        DatabricksDashboardToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksDashboardToWarehouseRel()],
    )
