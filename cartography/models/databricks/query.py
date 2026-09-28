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
class DatabricksQueryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Workspace-scoped identifier for the Databricks query."
    )
    query_id: PropertyRef = PropertyRef(
        "query_id", extra_index=True, description="Databricks query identifier."
    )
    display_name: PropertyRef = PropertyRef(
        "display_name", extra_index=True, description="Display name of the query."
    )
    warehouse_id: PropertyRef = PropertyRef(
        "warehouse_id",
        extra_index=True,
        description="Identifier of the SQL warehouse used by the query.",
    )
    query_text: PropertyRef = PropertyRef(
        "query_text", description="SQL text of the saved query."
    )
    owner_user_name: PropertyRef = PropertyRef(
        "owner_user_name", extra_index=True, description="User name of the query owner."
    )
    last_modifier_user_name: PropertyRef = PropertyRef(
        "last_modifier_user_name",
        description="User name of the principal that last modified the query.",
    )
    run_as_mode: PropertyRef = PropertyRef(
        "run_as_mode", description="Principal mode used when the query runs."
    )
    lifecycle_state: PropertyRef = PropertyRef(
        "lifecycle_state", description="Lifecycle state of the query."
    )
    parent_path: PropertyRef = PropertyRef(
        "parent_path", description="Workspace path of the query's parent folder."
    )
    create_time: PropertyRef = PropertyRef(
        "create_time", description="Timestamp when the query was created."
    )
    update_time: PropertyRef = PropertyRef(
        "update_time", description="Timestamp when the query was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksQueryToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksQuery)
class DatabricksQueryToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains this query resource."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksQueryToWorkspaceRelProperties = (
        DatabricksQueryToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksQueryToWarehouseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksQuery)-[:USES_WAREHOUSE]->(:DatabricksSqlWarehouse)
class DatabricksQueryToWarehouseRel(CartographyRelSchema):
    """A Databricks query uses a SQL warehouse."""

    target_node_label: str = "DatabricksSqlWarehouse"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("warehouse_scoped_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_WAREHOUSE"
    properties: DatabricksQueryToWarehouseRelProperties = (
        DatabricksQueryToWarehouseRelProperties()
    )


@dataclass(frozen=True)
class DatabricksQuerySchema(CartographyNodeSchema):
    """A saved Databricks SQL query."""

    label: str = "DatabricksQuery"
    properties: DatabricksQueryNodeProperties = DatabricksQueryNodeProperties()
    sub_resource_relationship: DatabricksQueryToWorkspaceRel = (
        DatabricksQueryToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksQueryToWarehouseRel()],
    )
