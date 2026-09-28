from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.databricks.extra_labels import DATABRICKS_ACL_OBJECT


@dataclass(frozen=True)
class DatabricksSqlWarehouseNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Workspace-scoped identifier for the Databricks SQL warehouse.",
    )
    warehouse_id: PropertyRef = PropertyRef(
        "warehouse_id",
        extra_index=True,
        description="Databricks SQL warehouse identifier.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the SQL warehouse."
    )
    state: PropertyRef = PropertyRef(
        "state", description="Current state of the SQL warehouse."
    )
    cluster_size: PropertyRef = PropertyRef(
        "cluster_size", description="Cluster size configured for the SQL warehouse."
    )
    size: PropertyRef = PropertyRef(
        "size", description="Reported size of the SQL warehouse."
    )
    warehouse_type: PropertyRef = PropertyRef(
        "warehouse_type", description="Type of the SQL warehouse."
    )
    enable_serverless_compute: PropertyRef = PropertyRef(
        "enable_serverless_compute",
        description="Whether serverless compute is enabled.",
    )
    enable_photon: PropertyRef = PropertyRef(
        "enable_photon", description="Whether the Photon engine is enabled."
    )
    auto_stop_mins: PropertyRef = PropertyRef(
        "auto_stop_mins", description="Idle minutes before automatic shutdown."
    )
    auto_resume: PropertyRef = PropertyRef(
        "auto_resume", description="Whether the SQL warehouse automatically resumes."
    )
    spot_instance_policy: PropertyRef = PropertyRef(
        "spot_instance_policy",
        description="Spot instance policy for the SQL warehouse.",
    )
    channel: PropertyRef = PropertyRef(
        "channel", description="Runtime release channel used by the SQL warehouse."
    )
    min_num_clusters: PropertyRef = PropertyRef(
        "min_num_clusters", description="Minimum number of clusters."
    )
    max_num_clusters: PropertyRef = PropertyRef(
        "max_num_clusters", description="Maximum number of clusters."
    )
    num_clusters: PropertyRef = PropertyRef(
        "num_clusters", description="Current number of clusters."
    )
    creator_name: PropertyRef = PropertyRef(
        "creator_name",
        extra_index=True,
        description="User name of the SQL warehouse creator.",
    )
    jdbc_url: PropertyRef = PropertyRef(
        "jdbc_url", description="JDBC connection URL for the SQL warehouse."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksSqlWarehouseToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksSqlWarehouse)
class DatabricksSqlWarehouseToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains this SQL warehouse resource."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksSqlWarehouseToWorkspaceRelProperties = (
        DatabricksSqlWarehouseToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksSqlWarehouseSchema(CartographyNodeSchema):
    """A Databricks SQL warehouse."""

    label: str = "DatabricksSqlWarehouse"
    properties: DatabricksSqlWarehouseNodeProperties = (
        DatabricksSqlWarehouseNodeProperties()
    )
    sub_resource_relationship: DatabricksSqlWarehouseToWorkspaceRel = (
        DatabricksSqlWarehouseToWorkspaceRel()
    )
    # ACL-target ontology label so the HAS_PERMISSION MatchLinks can target it.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABRICKS_ACL_OBJECT])
