from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DatabricksSqlWarehouseNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    warehouse_id: PropertyRef = PropertyRef("warehouse_id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    state: PropertyRef = PropertyRef("state")
    cluster_size: PropertyRef = PropertyRef("cluster_size")
    size: PropertyRef = PropertyRef("size")
    warehouse_type: PropertyRef = PropertyRef("warehouse_type")
    enable_serverless_compute: PropertyRef = PropertyRef("enable_serverless_compute")
    enable_photon: PropertyRef = PropertyRef("enable_photon")
    auto_stop_mins: PropertyRef = PropertyRef("auto_stop_mins")
    auto_resume: PropertyRef = PropertyRef("auto_resume")
    spot_instance_policy: PropertyRef = PropertyRef("spot_instance_policy")
    channel: PropertyRef = PropertyRef("channel")
    min_num_clusters: PropertyRef = PropertyRef("min_num_clusters")
    max_num_clusters: PropertyRef = PropertyRef("max_num_clusters")
    num_clusters: PropertyRef = PropertyRef("num_clusters")
    creator_name: PropertyRef = PropertyRef("creator_name", extra_index=True)
    jdbc_url: PropertyRef = PropertyRef("jdbc_url")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksSqlWarehouseToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksSqlWarehouse)
class DatabricksSqlWarehouseToWorkspaceRel(CartographyRelSchema):
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
    label: str = "DatabricksSqlWarehouse"
    properties: DatabricksSqlWarehouseNodeProperties = (
        DatabricksSqlWarehouseNodeProperties()
    )
    sub_resource_relationship: DatabricksSqlWarehouseToWorkspaceRel = (
        DatabricksSqlWarehouseToWorkspaceRel()
    )
