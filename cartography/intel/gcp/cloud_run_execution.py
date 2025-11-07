import logging

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.cloudrun.execution import GCPCloudRunExecutionSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_cloud_run_executions(client: Resource, job_name: str) -> list[dict]:
    executions: list[dict] = []
    request = client.projects().locations().jobs().executions().list(parent=job_name)
    while request is not None:
        response = request.execute()
        executions.extend(response.get("executions", []))
        request = (
            client.projects()
            .locations()
            .jobs()
            .executions()
            .list_next(
                previous_request=request,
                previous_response=response,
            )
        )
    return executions


def transform_executions(executions_data: list[dict], project_id: str) -> list[dict]:
    transformed: list[dict] = []
    for ex in executions_data:
        ex_id = ex.get("name")
        if not ex_id:
            continue
        status_data = ex.get("status", {})
        transformed.append(
            {
                "id": ex_id,
                "name": ex.get("name", "").split("/")[-1],
                "job": ex.get("name", "").rsplit("/executions/", 1)[0],
                "status": str(status_data.get("completionTime", "RUNNING")),
                "cancelled_count": status_data.get("cancelledCount"),
                "failed_count": status_data.get("failedCount"),
                "succeeded_count": status_data.get("succeededCount"),
                "project_id": project_id,
            },
        )
    return transformed


@timeit
def load_cloud_run_executions(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPCloudRunExecutionSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def cleanup_cloud_run_executions(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(GCPCloudRunExecutionSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_cloud_run_executions(
    neo4j_session: neo4j.Session,
    client: Resource,
    jobs_raw: list[dict],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(f"Syncing Cloud Run Executions for project {project_id}.")
    all_executions: list[dict] = []
    for job_raw in jobs_raw:
        job_name = job_raw.get("name")
        if not job_name:
            continue
        executions_raw = get_cloud_run_executions(client, job_name)
        all_executions.extend(transform_executions(executions_raw, project_id))

    load_cloud_run_executions(neo4j_session, all_executions, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["project_id"] = project_id
    cleanup_cloud_run_executions(neo4j_session, cleanup_job_params)
