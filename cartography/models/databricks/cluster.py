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
class DatabricksClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    cluster_id: PropertyRef = PropertyRef("cluster_id", extra_index=True)
    cluster_name: PropertyRef = PropertyRef("cluster_name", extra_index=True)
    state: PropertyRef = PropertyRef("state")
    spark_version: PropertyRef = PropertyRef("spark_version")
    runtime_engine: PropertyRef = PropertyRef("runtime_engine")
    node_type_id: PropertyRef = PropertyRef("node_type_id")
    driver_node_type_id: PropertyRef = PropertyRef("driver_node_type_id")
    num_workers: PropertyRef = PropertyRef("num_workers")
    autotermination_minutes: PropertyRef = PropertyRef("autotermination_minutes")
    cluster_source: PropertyRef = PropertyRef("cluster_source")
    data_security_mode: PropertyRef = PropertyRef("data_security_mode")
    single_user_name: PropertyRef = PropertyRef("single_user_name", extra_index=True)
    creator_user_name: PropertyRef = PropertyRef("creator_user_name", extra_index=True)
    driver_instance_pool_id: PropertyRef = PropertyRef(
        "driver_instance_pool_id", extra_index=True
    )
    instance_pool_id: PropertyRef = PropertyRef("instance_pool_id", extra_index=True)
    enable_local_disk_encryption: PropertyRef = PropertyRef(
        "enable_local_disk_encryption"
    )
    enable_elastic_disk: PropertyRef = PropertyRef("enable_elastic_disk")
    start_time: PropertyRef = PropertyRef("start_time")
    terminated_time: PropertyRef = PropertyRef("terminated_time")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksClusterToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksCluster)
class DatabricksClusterToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksClusterToWorkspaceRelProperties = (
        DatabricksClusterToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksClusterToPolicyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksCluster)-[:HAS_POLICY]->(:DatabricksClusterPolicy)
class DatabricksClusterToPolicyRel(CartographyRelSchema):
    target_node_label: str = "DatabricksClusterPolicy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("policy_id_scoped")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_POLICY"
    properties: DatabricksClusterToPolicyRelProperties = (
        DatabricksClusterToPolicyRelProperties()
    )


@dataclass(frozen=True)
class DatabricksClusterToInstancePoolRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksCluster)-[:USES_INSTANCE_POOL]->(:DatabricksInstancePool)
# Covers both worker and driver pools; a cluster can target each from a
# different pool, and the security/dependency implications are identical.
class DatabricksClusterToInstancePoolRel(CartographyRelSchema):
    target_node_label: str = "DatabricksInstancePool"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("instance_pool_ids_scoped", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_INSTANCE_POOL"
    properties: DatabricksClusterToInstancePoolRelProperties = (
        DatabricksClusterToInstancePoolRelProperties()
    )


@dataclass(frozen=True)
class DatabricksClusterSchema(CartographyNodeSchema):
    label: str = "DatabricksCluster"
    properties: DatabricksClusterNodeProperties = DatabricksClusterNodeProperties()
    sub_resource_relationship: DatabricksClusterToWorkspaceRel = (
        DatabricksClusterToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DatabricksClusterToPolicyRel(),
            DatabricksClusterToInstancePoolRel(),
        ],
    )
