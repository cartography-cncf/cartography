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
class DatabricksJobTaskNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Workspace-scoped identifier for the job task."
    )
    task_key: PropertyRef = PropertyRef(
        "task_key",
        extra_index=True,
        description="Key that identifies the task in its job.",
    )
    job_id: PropertyRef = PropertyRef(
        "job_id",
        extra_index=True,
        description="Databricks identifier of the job containing the task.",
    )
    task_type: PropertyRef = PropertyRef(
        "task_type", description="Type of workload performed by the task."
    )
    notebook_path: PropertyRef = PropertyRef(
        "notebook_path",
        extra_index=True,
        description="Workspace path of the notebook run by the task.",
    )
    notebook_scoped_id: PropertyRef = PropertyRef(
        "notebook_scoped_id",
        extra_index=True,
        description="Workspace-scoped identifier of the referenced notebook.",
    )
    existing_cluster_id: PropertyRef = PropertyRef(
        "existing_cluster_id",
        description="Identifier of the existing cluster used by the task.",
    )
    job_cluster_key: PropertyRef = PropertyRef(
        "job_cluster_key",
        description="Key of the job cluster used by the task.",
    )
    pipeline_id: PropertyRef = PropertyRef(
        "pipeline_id",
        extra_index=True,
        description="Identifier of the pipeline run by the task.",
    )
    warehouse_id: PropertyRef = PropertyRef(
        "warehouse_id",
        extra_index=True,
        description="Identifier of the SQL warehouse used by the task.",
    )
    run_job_id: PropertyRef = PropertyRef(
        "run_job_id",
        extra_index=True,
        description="Identifier of the job invoked by the task.",
    )
    disabled: PropertyRef = PropertyRef(
        "disabled", description="Whether the task is disabled."
    )
    run_if: PropertyRef = PropertyRef(
        "run_if", description="Condition that controls whether the task runs."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksJobTaskToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksJobTask)
class DatabricksJobTaskToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains the job task as a resource."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksJobTaskToWorkspaceRelProperties = (
        DatabricksJobTaskToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksJobTaskToJobRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksJob)-[:HAS_TASK]->(:DatabricksJobTask)
class DatabricksJobTaskToJobRel(CartographyRelSchema):
    """A Databricks job contains the task."""

    target_node_label: str = "DatabricksJob"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("job_scoped_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_TASK"
    properties: DatabricksJobTaskToJobRelProperties = (
        DatabricksJobTaskToJobRelProperties()
    )


@dataclass(frozen=True)
class DatabricksJobTaskToPipelineRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksJobTask)-[:RUNS_PIPELINE]->(:DatabricksPipeline)
class DatabricksJobTaskToPipelineRel(CartographyRelSchema):
    """A Databricks job task runs a pipeline."""

    target_node_label: str = "DatabricksPipeline"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("pipeline_scoped_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_PIPELINE"
    properties: DatabricksJobTaskToPipelineRelProperties = (
        DatabricksJobTaskToPipelineRelProperties()
    )


@dataclass(frozen=True)
class DatabricksJobTaskToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksJobTask)-[:USES_CLUSTER]->(:DatabricksCluster)
class DatabricksJobTaskToClusterRel(CartographyRelSchema):
    """A Databricks job task uses an existing cluster."""

    target_node_label: str = "DatabricksCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("existing_cluster_scoped_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_CLUSTER"
    properties: DatabricksJobTaskToClusterRelProperties = (
        DatabricksJobTaskToClusterRelProperties()
    )


@dataclass(frozen=True)
class DatabricksJobTaskToWarehouseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksJobTask)-[:USES_WAREHOUSE]->(:DatabricksSqlWarehouse)
class DatabricksJobTaskToWarehouseRel(CartographyRelSchema):
    """A Databricks job task uses a SQL warehouse."""

    target_node_label: str = "DatabricksSqlWarehouse"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("warehouse_scoped_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_WAREHOUSE"
    properties: DatabricksJobTaskToWarehouseRelProperties = (
        DatabricksJobTaskToWarehouseRelProperties()
    )


@dataclass(frozen=True)
class DatabricksJobTaskSchema(CartographyNodeSchema):
    """A task within a Databricks job."""

    label: str = "DatabricksJobTask"
    properties: DatabricksJobTaskNodeProperties = DatabricksJobTaskNodeProperties()
    sub_resource_relationship: DatabricksJobTaskToWorkspaceRel = (
        DatabricksJobTaskToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DatabricksJobTaskToJobRel(),
            DatabricksJobTaskToPipelineRel(),
            DatabricksJobTaskToClusterRel(),
            DatabricksJobTaskToWarehouseRel(),
        ],
    )
