import logging
import re
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import neo4j
from google.api_core.exceptions import PermissionDenied
from google.auth.credentials import Credentials as GoogleCredentials
from google.cloud.run_v2 import ExecutionsClient
from google.cloud.run_v2 import JobsClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.cloudrun.job import get_jobs
from cartography.intel.gcp.util import proto_message_to_dict
from cartography.models.gcp.cloudrun.execution import GCPCloudRunExecutionSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_DEFAULT_CLOUD_RUN_EXECUTION_WORKERS = 10


def _get_executions_for_job(
    client: ExecutionsClient,
    job_name: str,
) -> list[dict]:
    return [
        proto_message_to_dict(execution)
        for execution in client.list_executions(parent=job_name)
    ]


@timeit
def get_executions(
    client: ExecutionsClient,
    project_id: str,
    location: str = "-",
    credentials: Optional[GoogleCredentials] = None,
    jobs_raw: list[dict] | None = None,
    max_workers: int = _DEFAULT_CLOUD_RUN_EXECUTION_WORKERS,
    jobs_client: JobsClient | None = None,
) -> list[dict] | None:
    """
    Gets GCP Cloud Run Executions for a project and location.

    Executions are nested under jobs, so we need to:
    1. Discover locations (if querying all locations)
    2. For each location, get all jobs
    3. For each job, get all executions
    """
    if jobs_raw is None:
        if jobs_client is None:
            raise ValueError("jobs_client is required when jobs_raw is not provided.")
        jobs_raw = get_jobs(
            jobs_client,
            project_id,
            location=location,
            credentials=credentials,
        )
        if jobs_raw is None:
            return None

    job_names = [job.get("name", "") for job in jobs_raw if job.get("name")]
    if not job_names:
        return []

    if len(job_names) < 2 or max_workers <= 1:
        executions: list[dict] = []
        for job_name in job_names:
            try:
                executions.extend(_get_executions_for_job(client, job_name))
            except PermissionDenied:
                logger.warning(
                    "Permission denied listing Cloud Run executions for job %s. Skipping job.",
                    job_name,
                )
        return executions

    threaded_executions: list[dict] = []
    with ThreadPoolExecutor(
        max_workers=min(max_workers, len(job_names)),
    ) as executor:
        futures = {
            executor.submit(_get_executions_for_job, client, job_name): job_name
            for job_name in job_names
        }
        for future in as_completed(futures):
            try:
                threaded_executions.extend(future.result())
            except PermissionDenied:
                logger.warning(
                    "Permission denied listing Cloud Run executions for job %s. Skipping job.",
                    futures[future],
                )
                continue

    return threaded_executions


def transform_executions(executions_data: list[dict], project_id: str) -> list[dict]:
    """
    Transforms the list of Cloud Run Execution dicts for ingestion.
    """
    transformed: list[dict] = []
    for execution in executions_data:
        # Full resource name: projects/{project}/locations/{location}/jobs/{job}/executions/{execution}
        full_name = execution.get("name", "")

        # Extract location, job name, and short name from the full resource name
        name_match = re.match(
            r"projects/[^/]+/locations/([^/]+)/jobs/([^/]+)/executions/([^/]+)",
            full_name,
        )
        location = name_match.group(1) if name_match else None
        job_short_name = name_match.group(2) if name_match else None
        short_name = name_match.group(3) if name_match else None

        # Construct the full job resource name
        job_full_name = None
        if location and job_short_name:
            job_full_name = (
                f"projects/{project_id}/locations/{location}/jobs/{job_short_name}"
            )

        # Get task counts
        cancelled_count = execution.get("cancelledCount", 0)
        failed_count = execution.get("failedCount", 0)
        succeeded_count = execution.get("succeededCount", 0)

        transformed.append(
            {
                "id": full_name,
                "name": short_name,
                "job": job_full_name,
                "cancelled_count": cancelled_count,
                "failed_count": failed_count,
                "succeeded_count": succeeded_count,
                "project_id": project_id,
            },
        )
    return transformed


@timeit
def load_executions(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    """
    Loads GCPCloudRunExecution nodes and their relationships.
    """
    load(
        neo4j_session,
        GCPCloudRunExecutionSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def cleanup_executions(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """
    Cleans up stale Cloud Run executions.
    """
    GraphJob.from_node_schema(GCPCloudRunExecutionSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_executions(
    neo4j_session: neo4j.Session,
    client: ExecutionsClient,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
    credentials: Optional[GoogleCredentials] = None,
    jobs_raw: list[dict] | None = None,
    jobs_client: JobsClient | None = None,
) -> None:
    """
    Syncs GCP Cloud Run Executions for a project.
    """
    logger.info(f"Syncing Cloud Run Executions for project {project_id}.")
    executions_raw = get_executions(
        client,
        project_id,
        credentials=credentials,
        jobs_raw=jobs_raw,
        jobs_client=jobs_client,
    )
    if executions_raw is not None:
        if not executions_raw:
            logger.info(f"No Cloud Run executions found for project {project_id}.")

        executions = transform_executions(executions_raw, project_id)
        load_executions(neo4j_session, executions, project_id, update_tag)

        cleanup_job_params = common_job_parameters.copy()
        cleanup_job_params["project_id"] = project_id
        cleanup_executions(neo4j_session, cleanup_job_params)
