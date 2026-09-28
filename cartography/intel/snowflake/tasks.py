"""Snowflake tasks: scheduled SQL and the DAGs built out of it."""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.names import split_qualified_name
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import schedule_to_text
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import sf_path_segment
from cartography.intel.snowflake.util import skip_or_raise_http
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.task import SnowflakeTaskSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Tasks in one schema, or None when the schema is not readable."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}/tasks",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        return None


def _predecessor_ids(
    predecessors: list[str] | None,
    database_name: str,
    schema_name: str,
    account_id: str,
) -> list[str]:
    """Resolve a task's predecessor names to the ids of the predecessor task nodes.

    Snowflake reports a predecessor either bare (``ROOT_TASK``) or fully qualified,
    depending on how the task was declared, so a bare name is qualified with the
    dependent task's own database and schema. A task graph cannot span schemas, so
    that is always the right parent. Each name is then rebuilt with ``sf_fqn`` to
    guarantee the id comes out byte-identical to the predecessor task's own id.
    """
    ids: list[str] = []
    for predecessor in predecessors or []:
        parts = split_qualified_name(predecessor)
        if len(parts) == 1:
            parts = [database_name, schema_name, parts[0]]
        if len(parts) != 3 or not all(parts):
            logger.warning(
                "Skipping Snowflake task predecessor %s: it is neither a bare name "
                "nor a three-part name.",
                predecessor,
            )
            continue
        ids.append(sf_id(account_id, "task", sf_fqn(*parts)))
    return ids


def transform(
    tasks: list[dict[str, Any]],
    schema: dict[str, Any],
    account_id: str,
) -> list[dict[str, Any]]:
    database_name = schema["database_name"]
    schema_name = schema["name"]
    transformed: list[dict[str, Any]] = []

    for task in tasks:
        name = task["name"]
        qualified_name = sf_fqn(database_name, schema_name, name)
        warehouse = task.get("warehouse")
        error_integration = task.get("error_integration")
        success_integration = task.get("success_integration")
        owner = task.get("owner")
        # A caller-rights task runs with whatever privileges the resuming role
        # holds, so no single role can be named and the edge is suppressed. A task
        # owned by a database role points at a different label entirely.
        owner_role_id = (
            sf_id(account_id, "role", owner)
            if owner
            and task.get("execute_as") == "OWNER"
            and task.get("owner_role_type") != "DATABASE_ROLE"
            else None
        )
        transformed.append(
            {
                "id": sf_id(account_id, "task", qualified_name),
                "name": name,
                "qualified_name": qualified_name,
                "database_name": database_name,
                "schema_name": schema_name,
                "parent_schema_id": schema["id"],
                "warehouse": warehouse,
                "warehouse_id": (
                    sf_id(account_id, "warehouse", sf_fqn(warehouse))
                    if warehouse
                    else None
                ),
                "schedule": schedule_to_text(task.get("schedule")),
                "state": task.get("state"),
                "definition": task.get("definition"),
                "predecessors": task.get("predecessors"),
                "predecessor_ids": _predecessor_ids(
                    task.get("predecessors"), database_name, schema_name, account_id
                ),
                "condition": task.get("condition"),
                "allow_overlapping_execution": task.get("allow_overlapping_execution"),
                "error_integration": error_integration,
                "error_integration_id": (
                    sf_id(
                        account_id,
                        "notification_integration",
                        sf_fqn(error_integration),
                    )
                    if error_integration
                    else None
                ),
                "success_integration": success_integration,
                "success_integration_id": (
                    sf_id(
                        account_id,
                        "notification_integration",
                        sf_fqn(success_integration),
                    )
                    if success_integration
                    else None
                ),
                "execute_as": task.get("execute_as"),
                "suspend_task_after_num_failures": task.get(
                    "suspend_task_after_num_failures"
                ),
                "target_completion_interval": task.get("target_completion_interval"),
                "user_task_managed_initial_warehouse_size": task.get(
                    "user_task_managed_initial_warehouse_size"
                ),
                "owner": owner,
                "owner_role_id": owner_role_id,
                "owner_role_type": task.get("owner_role_type"),
                "comment": task.get("comment"),
                "created_on": iso_to_datetime(task.get("created_on")),
            },
        )
    return transformed


def load_tasks(
    neo4j_session: neo4j.Session,
    tasks: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    """Load task nodes, then load them again to wire the task-to-task edges.

    A task's PRECEDED_BY target is another task, so the whole batch has to exist
    as nodes before any predecessor edge can match. One pass would silently drop
    every edge whose predecessor happens to be processed later.
    """
    for _pass in range(2):
        load(
            neo4j_session,
            SnowflakeTaskSchema(),
            tasks,
            lastupdated=update_tag,
            ACCOUNT_ID=account_id,
        )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeTaskSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync every task in every readable schema.

    Returns whether the walk was complete. When a schema could not be read, the
    caller skips task cleanup rather than deleting nodes it merely failed to
    re-read this run.
    """
    account_id = client.account_id
    tasks: list[dict[str, Any]] = []
    complete = True

    for schema in schemas:
        listing = get(client, schema["database_name"], schema["name"])
        if listing is None:
            complete = False
            continue
        tasks.extend(transform(listing, schema, account_id))

    logger.info(
        "Loading %d Snowflake tasks for account %s.",
        len(tasks),
        account_id,
    )
    load_tasks(neo4j_session, tasks, account_id, common_job_parameters["UPDATE_TAG"])

    if not complete:
        logger.warning(
            "Some Snowflake schemas could not be read for tasks; skipping task "
            "cleanup so still-valid nodes are not deleted.",
        )
    return complete
