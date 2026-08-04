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
class DatabricksJobNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Workspace-scoped identifier for the job."
    )
    job_id: PropertyRef = PropertyRef(
        "job_id", extra_index=True, description="Databricks job identifier."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the job."
    )
    creator_user_name: PropertyRef = PropertyRef(
        "creator_user_name",
        extra_index=True,
        description="User who created the job.",
    )
    run_as_user_name: PropertyRef = PropertyRef(
        "run_as_user_name",
        extra_index=True,
        description="User name or application identifier of the run-as principal.",
    )
    format: PropertyRef = PropertyRef(
        "format", description="Job format, such as single-task or multi-task."
    )
    max_concurrent_runs: PropertyRef = PropertyRef(
        "max_concurrent_runs",
        description="Maximum number of concurrent active runs.",
    )
    timeout_seconds: PropertyRef = PropertyRef(
        "timeout_seconds", description="Maximum run duration in seconds."
    )
    continuous: PropertyRef = PropertyRef(
        "continuous", description="Whether the job uses continuous execution."
    )
    schedule_quartz_cron_expression: PropertyRef = PropertyRef(
        "schedule_quartz_cron_expression",
        description="Quartz cron expression for the job schedule.",
    )
    schedule_timezone_id: PropertyRef = PropertyRef(
        "schedule_timezone_id", description="Time zone used by the job schedule."
    )
    schedule_pause_status: PropertyRef = PropertyRef(
        "schedule_pause_status", description="Pause state of the job schedule."
    )
    created_time: PropertyRef = PropertyRef(
        "created_time", description="Timestamp when the job was created."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksJobToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksJob)
class DatabricksJobToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains the job as a resource."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksJobToWorkspaceRelProperties = (
        DatabricksJobToWorkspaceRelProperties()
    )


# The run-as edges match by the workspace-scoped principal node id resolved in
# the intel layer (see util.get_run_as_principal_index), never the bare name,
# so a federated user_name shared across workspaces cannot attach the edge to
# the wrong principal. A job runs as exactly one principal, so only one of the
# two edges fires per job.


@dataclass(frozen=True)
class DatabricksJobToRunAsUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksJob)-[:RUN_AS]->(:DatabricksUser)
class DatabricksJobToRunAsUserRel(CartographyRelSchema):
    """A Databricks job runs as a Databricks user."""

    target_node_label: str = "DatabricksUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("run_as_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUN_AS"
    properties: DatabricksJobToRunAsUserRelProperties = (
        DatabricksJobToRunAsUserRelProperties()
    )


@dataclass(frozen=True)
class DatabricksJobToRunAsSPRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksJob)-[:RUN_AS]->(:DatabricksServicePrincipal)
class DatabricksJobToRunAsSPRel(CartographyRelSchema):
    """A Databricks job runs as a Databricks service principal."""

    target_node_label: str = "DatabricksServicePrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("run_as_sp_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUN_AS"
    properties: DatabricksJobToRunAsSPRelProperties = (
        DatabricksJobToRunAsSPRelProperties()
    )


@dataclass(frozen=True)
class DatabricksJobSchema(CartographyNodeSchema):
    """A Databricks job that defines an automated workload."""

    label: str = "DatabricksJob"
    properties: DatabricksJobNodeProperties = DatabricksJobNodeProperties()
    sub_resource_relationship: DatabricksJobToWorkspaceRel = (
        DatabricksJobToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DatabricksJobToRunAsUserRel(),
            DatabricksJobToRunAsSPRel(),
        ],
    )
    # ACL-target ontology label so the HAS_PERMISSION MatchLinks can target it.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABRICKS_ACL_OBJECT])
