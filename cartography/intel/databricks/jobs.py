from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import epoch_ms_to_datetime
from cartography.intel.databricks.util import get_run_as_principal_index
from cartography.intel.databricks.util import scoped_id
from cartography.models.databricks.job import DatabricksJobSchema
from cartography.models.databricks.job_task import DatabricksJobTaskSchema
from cartography.util import timeit

# Task settings carry exactly one of these blocks; the key names the task type.
_TASK_TYPE_KEYS = (
    "notebook_task",
    "spark_jar_task",
    "spark_python_task",
    "python_wheel_task",
    "pipeline_task",
    "sql_task",
    "dbt_task",
    "run_job_task",
    "condition_task",
    "for_each_task",
)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    jobs = get(api_session)
    principals = get_run_as_principal_index(neo4j_session, workspace_id)
    transformed_jobs = transform_jobs(jobs, workspace_id, principals)
    transformed_tasks = transform_tasks(jobs, workspace_id)
    load_jobs(
        neo4j_session,
        transformed_jobs,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    load_tasks(
        neo4j_session,
        transformed_tasks,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    """List jobs with their task graph expanded (paginated via page_token)."""
    results: list[dict[str, Any]] = []
    params: dict[str, Any] = {"limit": 100, "expand_tasks": "true"}
    seen_tokens: set[str] = set()
    while True:
        response = api_session.get("/api/2.1/jobs/list", params=params)
        results.extend(response.get("jobs", []) or [])
        if not response.get("has_more"):
            break
        next_token = response.get("next_page_token")
        # has_more with no token is a malformed response: breaking here would
        # silently drop the remaining jobs and let cleanup delete their nodes.
        if not next_token:
            raise ValueError(
                "Databricks jobs list reported has_more but no next_page_token",
            )
        if next_token in seen_tokens:
            raise ValueError(
                f"Databricks jobs list repeated page token {next_token!r}; "
                "aborting to avoid an infinite loop.",
            )
        seen_tokens.add(next_token)
        params = {"limit": 100, "expand_tasks": "true", "page_token": next_token}
    return results


def _task_type(task: dict[str, Any]) -> str | None:
    for key in _TASK_TYPE_KEYS:
        if task.get(key) is not None:
            return key
    return None


@timeit
def transform_jobs(
    jobs: list[dict[str, Any]],
    workspace_id: str,
    principals: dict[str, tuple[str, bool]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for j in jobs:
        job_id = j.get("job_id")
        if not job_id:
            raise ValueError("Databricks job returned with empty job_id")
        settings = j.get("settings") or {}
        schedule = settings.get("schedule") or {}
        run_as_name = j.get("run_as_user_name")
        # A job runs as exactly one principal; route the scoped id to the
        # user or service-principal field so only the matching RUN_AS edge fires.
        resolved = principals.get(run_as_name) if run_as_name else None
        run_as_id, is_sp = resolved if resolved else (None, False)
        result.append(
            {
                "id": scoped_id(workspace_id, str(job_id)),
                "job_id": str(job_id),
                "name": settings.get("name"),
                "creator_user_name": j.get("creator_user_name"),
                "run_as_user_name": run_as_name,
                "run_as_user_id": run_as_id if not is_sp else None,
                "run_as_sp_id": run_as_id if is_sp else None,
                "format": settings.get("format"),
                "max_concurrent_runs": settings.get("max_concurrent_runs"),
                "timeout_seconds": settings.get("timeout_seconds"),
                "continuous": bool(settings.get("continuous")),
                "schedule_quartz_cron_expression": schedule.get(
                    "quartz_cron_expression"
                ),
                "schedule_timezone_id": schedule.get("timezone_id"),
                "schedule_pause_status": schedule.get("pause_status"),
                "created_time": epoch_ms_to_datetime(j.get("created_time")),
            }
        )
    return result


@timeit
def transform_tasks(
    jobs: list[dict[str, Any]], workspace_id: str
) -> list[dict[str, Any]]:
    """Flatten every job's task graph into standalone task rows.

    Task ids are ``{workspace}/{job_id}/{task_key}`` so the same task_key reused
    across jobs stays distinct. Cross-resource ids (pipeline / cluster /
    warehouse) are workspace-scoped to match the nodes those syncs loaded.
    """
    result: list[dict[str, Any]] = []
    for j in jobs:
        job_id = j.get("job_id")
        if not job_id:
            continue
        job_id = str(job_id)
        job_scoped_id = scoped_id(workspace_id, job_id)
        settings = j.get("settings") or {}
        for task in settings.get("tasks", []) or []:
            task_key = task.get("task_key")
            if not task_key:
                continue
            pipeline_id = (task.get("pipeline_task") or {}).get("pipeline_id")
            warehouse_id = (task.get("sql_task") or {}).get("warehouse_id")
            run_job_id = (task.get("run_job_task") or {}).get("job_id")
            notebook_path = (task.get("notebook_task") or {}).get("notebook_path")
            existing_cluster_id = task.get("existing_cluster_id")
            result.append(
                {
                    "id": f"{job_scoped_id}/{task_key}",
                    "task_key": task_key,
                    "job_id": job_id,
                    "job_scoped_id": job_scoped_id,
                    "task_type": _task_type(task),
                    "notebook_path": notebook_path,
                    "notebook_scoped_id": (
                        scoped_id(workspace_id, notebook_path)
                        if notebook_path
                        else None
                    ),
                    "existing_cluster_id": existing_cluster_id,
                    "existing_cluster_scoped_id": (
                        scoped_id(workspace_id, existing_cluster_id)
                        if existing_cluster_id
                        else None
                    ),
                    "job_cluster_key": task.get("job_cluster_key"),
                    "pipeline_id": pipeline_id,
                    "pipeline_scoped_id": (
                        scoped_id(workspace_id, pipeline_id) if pipeline_id else None
                    ),
                    "warehouse_id": warehouse_id,
                    "warehouse_scoped_id": (
                        scoped_id(workspace_id, warehouse_id) if warehouse_id else None
                    ),
                    "run_job_id": str(run_job_id) if run_job_id else None,
                    "disabled": task.get("disabled"),
                    "run_if": task.get("run_if"),
                }
            )
    return result


@timeit
def load_jobs(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksJobSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def load_tasks(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksJobTaskSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    # Tasks first: they hang off jobs, so purge the children before the parents.
    GraphJob.from_node_schema(DatabricksJobTaskSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(DatabricksJobSchema(), common_job_parameters).run(
        neo4j_session
    )
