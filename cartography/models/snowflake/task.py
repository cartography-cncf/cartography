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
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeTaskNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the task."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True, description="Task name.")
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        description="Fully-qualified database.schema.task name.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name", description="Database containing the task."
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name", description="Schema containing the task."
    )
    warehouse: PropertyRef = PropertyRef(
        "warehouse",
        description=(
            "Name of the virtual warehouse the task runs on. Null for a serverless "
            "task, which Snowflake sizes itself."
        ),
    )
    schedule: PropertyRef = PropertyRef(
        "schedule",
        description=(
            "The task's schedule, as a cron expression or an interval. Null for a "
            "child task, which is triggered by its predecessors instead."
        ),
    )
    state: PropertyRef = PropertyRef(
        "state", description="Whether the task is started or suspended."
    )
    definition: PropertyRef = PropertyRef(
        "definition", description="SQL the task executes on every run."
    )
    predecessors: PropertyRef = PropertyRef(
        "predecessors",
        description="Fully-qualified names of the tasks that trigger this one.",
    )
    condition: PropertyRef = PropertyRef(
        "condition",
        description="WHEN expression that must hold for the run to go ahead.",
    )
    allow_overlapping_execution: PropertyRef = PropertyRef(
        "allow_overlapping_execution",
        description=(
            "Whether a new run may start while the previous one is still going, "
            "which lets a slow task pile up concurrent executions."
        ),
    )
    error_integration: PropertyRef = PropertyRef(
        "error_integration",
        description="Notification integration that receives the task's error notifications.",
    )
    success_integration: PropertyRef = PropertyRef(
        "success_integration",
        description="Notification integration that receives the task's success notifications.",
    )
    execute_as: PropertyRef = PropertyRef(
        "execute_as",
        description=(
            "Whether the task's SQL runs with the privileges of the task owner "
            "(OWNER) or of the role that resumed it (CALLER)."
        ),
    )
    suspend_task_after_num_failures: PropertyRef = PropertyRef(
        "suspend_task_after_num_failures",
        description=(
            "Number of consecutive failed runs after which Snowflake suspends the "
            "task. Zero means it is never suspended automatically."
        ),
    )
    target_completion_interval: PropertyRef = PropertyRef(
        "target_completion_interval",
        description="Duration Snowflake targets for a serverless run to complete in.",
    )
    user_task_managed_initial_warehouse_size: PropertyRef = PropertyRef(
        "user_task_managed_initial_warehouse_size",
        description="Initial compute size Snowflake uses for a serverless task's first run.",
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the task."
    )
    owner_role_type: PropertyRef = PropertyRef(
        "owner_role_type",
        description="Whether the owner is an account role or a database role.",
    )
    comment: PropertyRef = PropertyRef("comment", description="Task comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the task was created."
    )


@dataclass(frozen=True)
class SnowflakeTaskToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeTask)
class SnowflakeTaskToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the task as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeTaskToAccountRelProperties = (
        SnowflakeTaskToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeTaskToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeTask)
class SnowflakeTaskToSchemaRel(CartographyRelSchema):
    """A Snowflake schema holds the task in its namespace."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeTaskToSchemaRelProperties = (
        SnowflakeTaskToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeTaskToWarehouseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeTask)-[:USES_WAREHOUSE]->(:SnowflakeWarehouse)
class SnowflakeTaskToWarehouseRel(CartographyRelSchema):
    """A Snowflake task runs its SQL on this virtual warehouse."""

    target_node_label: str = "SnowflakeWarehouse"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("warehouse_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_WAREHOUSE"
    properties: SnowflakeTaskToWarehouseRelProperties = (
        SnowflakeTaskToWarehouseRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeTaskToPredecessorRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeTask)-[:PRECEDED_BY]->(:SnowflakeTask)
class SnowflakeTaskToPredecessorRel(CartographyRelSchema):
    """A Snowflake task only runs once this upstream task has finished.

    Chaining tasks this way builds a directed acyclic graph rooted at the one
    scheduled task, so following these edges upwards reveals what actually
    triggers a given piece of SQL.
    """

    target_node_label: str = "SnowflakeTask"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("predecessor_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PRECEDED_BY"
    properties: SnowflakeTaskToPredecessorRelProperties = (
        SnowflakeTaskToPredecessorRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeTaskToOwnerRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeTask)-[:ASSUMES]->(:SnowflakeRole)
class SnowflakeTaskToOwnerRoleRel(CartographyRelSchema):
    """A Snowflake task executes with the privileges of its owning role.

    Only present for an owner-rights task. A caller-rights task instead runs with
    the privileges of whichever role resumed it, so no single role can be named.
    """

    target_node_label: str = "SnowflakeRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_role_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUMES"
    properties: SnowflakeTaskToOwnerRoleRelProperties = (
        SnowflakeTaskToOwnerRoleRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeTaskToErrorIntegrationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeTask)-[:NOTIFIES]->(:SnowflakeNotificationIntegration)
class SnowflakeTaskToErrorIntegrationRel(CartographyRelSchema):
    """A Snowflake task sends its error notifications through this integration."""

    target_node_label: str = "SnowflakeNotificationIntegration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("error_integration_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "NOTIFIES"
    properties: SnowflakeTaskToErrorIntegrationRelProperties = (
        SnowflakeTaskToErrorIntegrationRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeTaskToSuccessIntegrationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeTask)-[:NOTIFIES]->(:SnowflakeNotificationIntegration)
class SnowflakeTaskToSuccessIntegrationRel(CartographyRelSchema):
    """A Snowflake task sends its success notifications through this integration."""

    target_node_label: str = "SnowflakeNotificationIntegration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("success_integration_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "NOTIFIES"
    properties: SnowflakeTaskToSuccessIntegrationRelProperties = (
        SnowflakeTaskToSuccessIntegrationRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeTaskSchema(CartographyNodeSchema):
    """Represents a Snowflake task: scheduled or DAG-triggered SQL running inside the account."""

    label: str = "SnowflakeTask"
    properties: SnowflakeTaskNodeProperties = SnowflakeTaskNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakeTaskToAccountRel = SnowflakeTaskToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeTaskToSchemaRel(),
            SnowflakeTaskToWarehouseRel(),
            SnowflakeTaskToPredecessorRel(),
            SnowflakeTaskToOwnerRoleRel(),
            SnowflakeTaskToErrorIntegrationRel(),
            SnowflakeTaskToSuccessIntegrationRel(),
        ],
    )
