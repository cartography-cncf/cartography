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
from cartography.models.databricks.extra_labels import DATABRICKS_ACL_OBJECT


@dataclass(frozen=True)
class DatabricksClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Workspace-scoped identifier for the cluster."
    )
    cluster_id: PropertyRef = PropertyRef(
        "cluster_id", extra_index=True, description="Databricks cluster identifier."
    )
    cluster_name: PropertyRef = PropertyRef(
        "cluster_name", extra_index=True, description="Name of the cluster."
    )
    state: PropertyRef = PropertyRef(
        "state", description="Current lifecycle state of the cluster."
    )
    spark_version: PropertyRef = PropertyRef(
        "spark_version", description="Databricks Runtime version used by the cluster."
    )
    runtime_engine: PropertyRef = PropertyRef(
        "runtime_engine", description="Runtime engine used by the cluster."
    )
    node_type_id: PropertyRef = PropertyRef(
        "node_type_id", description="Worker node type used by the cluster."
    )
    driver_node_type_id: PropertyRef = PropertyRef(
        "driver_node_type_id", description="Driver node type used by the cluster."
    )
    num_workers: PropertyRef = PropertyRef(
        "num_workers", description="Number of worker nodes in the cluster."
    )
    autotermination_minutes: PropertyRef = PropertyRef(
        "autotermination_minutes",
        description="Minutes of inactivity before the cluster terminates automatically.",
    )
    cluster_source: PropertyRef = PropertyRef(
        "cluster_source", description="Source that created the cluster."
    )
    data_security_mode: PropertyRef = PropertyRef(
        "data_security_mode", description="Data security mode of the cluster."
    )
    single_user_name: PropertyRef = PropertyRef(
        "single_user_name",
        extra_index=True,
        description="User assigned to a single-user cluster.",
    )
    creator_user_name: PropertyRef = PropertyRef(
        "creator_user_name",
        extra_index=True,
        description="User who created the cluster.",
    )
    driver_instance_pool_id: PropertyRef = PropertyRef(
        "driver_instance_pool_id",
        extra_index=True,
        description="Instance pool identifier used for the driver node.",
    )
    instance_pool_id: PropertyRef = PropertyRef(
        "instance_pool_id",
        extra_index=True,
        description="Instance pool identifier used for worker nodes.",
    )
    enable_local_disk_encryption: PropertyRef = PropertyRef(
        "enable_local_disk_encryption",
        description="Whether local disks are encrypted.",
    )
    enable_elastic_disk: PropertyRef = PropertyRef(
        "enable_elastic_disk",
        description="Whether elastic disk autoscaling is enabled.",
    )
    start_time: PropertyRef = PropertyRef(
        "start_time", description="Timestamp when the cluster was started."
    )
    terminated_time: PropertyRef = PropertyRef(
        "terminated_time", description="Timestamp when the cluster was terminated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksClusterToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksCluster)
class DatabricksClusterToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains the cluster as a resource."""

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
    """A Databricks cluster uses a cluster policy."""

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
    """A Databricks cluster uses an instance pool for driver or worker nodes."""

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
    """A Databricks compute cluster."""

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
    # ACL-target ontology label so the HAS_PERMISSION MatchLinks can target it.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABRICKS_ACL_OBJECT])
