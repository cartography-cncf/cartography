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


@dataclass(frozen=True)
class DatabricksJobNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    job_id: PropertyRef = PropertyRef("job_id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    creator_user_name: PropertyRef = PropertyRef("creator_user_name", extra_index=True)
    run_as_user_name: PropertyRef = PropertyRef("run_as_user_name", extra_index=True)
    format: PropertyRef = PropertyRef("format")
    max_concurrent_runs: PropertyRef = PropertyRef("max_concurrent_runs")
    timeout_seconds: PropertyRef = PropertyRef("timeout_seconds")
    continuous: PropertyRef = PropertyRef("continuous")
    schedule_quartz_cron_expression: PropertyRef = PropertyRef(
        "schedule_quartz_cron_expression"
    )
    schedule_timezone_id: PropertyRef = PropertyRef("schedule_timezone_id")
    schedule_pause_status: PropertyRef = PropertyRef("schedule_pause_status")
    created_time: PropertyRef = PropertyRef("created_time")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksJobToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksJob)
class DatabricksJobToWorkspaceRel(CartographyRelSchema):
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
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DatabricksAclObject"])
