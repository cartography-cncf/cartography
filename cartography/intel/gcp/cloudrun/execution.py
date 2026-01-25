import logging
import re

import neo4j
from google.api_core.exceptions import PermissionDenied
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.cloudrun.util import discover_cloud_run_locations
from cartography.models.gcp.cloudrun.execution import GCPCloudRunExecutionSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_executions(
    client: Resource, project_id: str, location: str = "-"
) -> list[dict]:
    """
    Gets GCP Cloud Run Executions for a project and location.

    Executions are nested under jobs, so we need to:
    1. Discover locations (if querying all locations)
    2. For each location, get all jobs
    3. For each job, get all executions
    """
    executions: list[dict] = []
    try:
        # Determine which locations to query
        if location == "-":
            # Discover all Cloud Run locations for this project
            locations = discover_cloud_run_locations(client, project_id)
        else:
            # Query specific location
            locations = {f"projects/{project_id}/locations/{location}"}

        # For each location, get jobs and their executions
        for loc_name in locations:
            # Get all jobs in this location
            jobs_request = client.projects().locations().jobs().list(parent=loc_name)
            while jobs_request is not None:
                jobs_response = jobs_request.execute()
                jobs = jobs_response.get("jobs", [])

                # For each job, get its executions
                for job in jobs:
                    job_name = job.get("name", "")
                    executions_request = (
                        client.projects()
                        .locations()
                        .jobs()
                        .executions()
                        .list(parent=job_name)
                    )

                    while executions_request is not None:
                        executions_response = executions_request.execute()
                        executions.extend(executions_response.get("executions", []))
                        executions_request = (
                            client.projects()
                            .locations()
                            .jobs()
                            .executions()
                            .list_next(
                                previous_request=executions_request,
                                previous_response=executions_response,
                            )
                        )

                jobs_request = (
                    client.projects()
                    .locations()
                    .jobs()
                    .list_next(
                        previous_request=jobs_request,
                        previous_response=jobs_response,
                    )
                )

        return executions
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            f"Failed to get Cloud Run executions for project {project_id} due to permissions or auth error: {e}",
        )
        raise


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
    client: Resource,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Syncs GCP Cloud Run Executions for a project.
    """
    logger.info(f"Syncing Cloud Run Executions for project {project_id}.")
    executions_raw = get_executions(client, project_id)
    if not executions_raw:
        logger.info(f"No Cloud Run executions found for project {project_id}.")

    executions = transform_executions(executions_raw, project_id)
    load_executions(neo4j_session, executions, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["project_id"] = project_id
    cleanup_executions(neo4j_session, cleanup_job_params)
