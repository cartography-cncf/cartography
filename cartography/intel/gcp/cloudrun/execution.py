import logging
import re

import neo4j
from google.api_core.exceptions import PermissionDenied
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.cloudrun.execution import GCPCloudRunExecutionSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_executions(
    client: Resource, project_id: str, location: str = "-"
) -> list[dict]:
    """
    Gets GCP Cloud Run Executions for a project and location.

    :param client: The Cloud Run API client
    :param project_id: The GCP project ID
    :param location: The location to query. Use "-" to query all locations (default)
    :return: List of Cloud Run Execution dictionaries
    """
    executions: list[dict] = []
    try:
        parent = f"projects/{project_id}/locations/{location}"
        request = client.executions().list(parent=parent)
        while request is not None:
            response = request.execute()
            executions.extend(response.get("executions", []))
            request = client.executions().list_next(
                previous_request=request,
                previous_response=response,
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

    :param executions_data: Raw execution data from the Cloud Run API
    :param project_id: The GCP project ID
    :return: Transformed list of execution dictionaries
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

        # Get status - completion condition
        status = execution.get("completionStatus")

        # Get task counts
        cancelled_count = execution.get("cancelledCount", 0)
        failed_count = execution.get("failedCount", 0)
        succeeded_count = execution.get("succeededCount", 0)

        transformed.append(
            {
                "id": full_name,
                "name": short_name,
                "job": job_full_name,
                "status": status,
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

    :param neo4j_session: The Neo4j session
    :param data: Transformed execution data
    :param project_id: The GCP project ID
    :param update_tag: Timestamp for tracking updates
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

    :param neo4j_session: The Neo4j session
    :param common_job_parameters: Common job parameters for cleanup
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

    :param neo4j_session: The Neo4j session
    :param client: The Cloud Run API client
    :param project_id: The GCP project ID
    :param update_tag: Timestamp for tracking updates
    :param common_job_parameters: Common job parameters for cleanup
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
