import logging
import re

import neo4j
from google.auth.credentials import Credentials as GoogleCredentials

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.clients import build_cloud_run_execution_client
from cartography.intel.gcp.cloudrun.util import fetch_cloud_run_resources_for_locations
from cartography.intel.gcp.cloudrun.util import list_cloud_run_resources_for_location
from cartography.models.gcp.cloudrun.execution import GCPCloudRunExecutionSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_executions(
    project_id: str,
    locations: list[str],
    credentials: GoogleCredentials,
) -> list[dict]:
    """
    Get GCP Cloud Run Executions for a project across cached locations.
    """

    client = build_cloud_run_execution_client(credentials=credentials)

    def fetch_for_location(location: str) -> list[dict]:
        return list_cloud_run_resources_for_location(
            fetcher=lambda **kw: client.list_executions(
                parent=f"{location}/jobs/-",
                **kw,
            ),
            resource_type="executions",
            location=location,
            project_id=project_id,
        )

    return fetch_cloud_run_resources_for_locations(
        locations=locations,
        project_id=project_id,
        resource_type="executions",
        fetch_for_location=fetch_for_location,
    )


def transform_executions(executions_data: list[dict], project_id: str) -> list[dict]:
    """
    Transform the list of Cloud Run Execution dicts for ingestion.
    """
    transformed: list[dict] = []
    for execution in executions_data:
        full_name = execution.get("name", "")
        name_match = re.match(
            r"projects/[^/]+/locations/([^/]+)/jobs/([^/]+)/executions/([^/]+)",
            full_name,
        )
        location = name_match.group(1) if name_match else None
        job_short_name = name_match.group(2) if name_match else None
        short_name = name_match.group(3) if name_match else None

        job_full_name = None
        if location and job_short_name:
            job_full_name = (
                f"projects/{project_id}/locations/{location}/jobs/{job_short_name}"
            )

        transformed.append(
            {
                "id": full_name,
                "name": short_name,
                "job": job_full_name,
                "cancelled_count": execution.get("cancelledCount", 0),
                "failed_count": execution.get("failedCount", 0),
                "succeeded_count": execution.get("succeededCount", 0),
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
    Load GCPCloudRunExecution nodes and their relationships.
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
    Clean up stale Cloud Run executions.
    """
    GraphJob.from_node_schema(GCPCloudRunExecutionSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_executions(
    neo4j_session: neo4j.Session,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
    cloud_run_locations: list[str],
    credentials: GoogleCredentials,
) -> None:
    """
    Sync GCP Cloud Run Executions for a project.
    """
    logger.info("Syncing Cloud Run Executions for project %s.", project_id)
    executions_raw = get_executions(project_id, cloud_run_locations, credentials)
    if not executions_raw:
        logger.info("No Cloud Run executions found for project %s.", project_id)

    executions = transform_executions(executions_raw, project_id)
    load_executions(neo4j_session, executions, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["project_id"] = project_id
    cleanup_executions(neo4j_session, cleanup_job_params)
