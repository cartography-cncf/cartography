import logging
import re
from typing import Optional

import neo4j
from google.api_core.exceptions import PermissionDenied
from google.auth.credentials import Credentials as GoogleCredentials
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.cloudrun.util import discover_cloud_run_locations
from cartography.intel.gcp.labels import sync_labels
from cartography.models.gcp.cloudrun.job import GCPCloudRunJobSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_jobs(
    client: Resource,
    project_id: str,
    location: str = "-",
    credentials: Optional[GoogleCredentials] = None,
) -> list[dict]:
    """
    Gets GCP Cloud Run Jobs for a project and location.
    """
    jobs: list[dict] = []
    try:
        # Determine which locations to query
        if location == "-":
            # Discover all Cloud Run locations for this project
            locations = discover_cloud_run_locations(
                client,
                project_id,
                credentials=credentials,
            )
        else:
            # Query specific location
            locations = {f"projects/{project_id}/locations/{location}"}

        # Query jobs for each location
        for loc_name in locations:
            try:
                request = client.projects().locations().jobs().list(parent=loc_name)
                while request is not None:
                    response = request.execute()
                    jobs.extend(response.get("jobs", []))
                    request = (
                        client.projects()
                        .locations()
                        .jobs()
                        .list_next(
                            previous_request=request,
                            previous_response=response,
                        )
                    )
            except HttpError as e:
                # Only skip 403 permission errors (e.g., restricted regions)
                # Re-raise other errors (429, 500, etc.) to surface systemic failures
                if e.resp.status == 403:
                    logger.warning(
                        f"Permission denied listing Cloud Run jobs in {loc_name}. Skipping location.",
                    )
                    continue
                raise

        return jobs
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            f"Failed to get Cloud Run jobs for project {project_id} due to permissions or auth error: {e}",
        )
        raise


def transform_jobs(jobs_data: list[dict], project_id: str) -> list[dict]:
    """
    Transforms the list of Cloud Run Job dicts for ingestion.
    """
    transformed: list[dict] = []
    for job in jobs_data:
        # Full resource name: projects/{project}/locations/{location}/jobs/{job}
        full_name = job.get("name", "")

        # Extract location and short name from the full resource name
        name_match = re.match(
            r"projects/[^/]+/locations/([^/]+)/jobs/([^/]+)",
            full_name,
        )
        location = name_match.group(1) if name_match else None
        short_name = name_match.group(2) if name_match else None

        # Get container image from template.template.containers[0].image
        container_image = None
        image_digest = None
        template = job.get("template", {})
        task_template = template.get("template", {})
        containers = task_template.get("containers", [])
        if containers and len(containers) > 0:
            container_image = containers[0].get("image")
            try:
                image_digest = (
                    container_image.split("@")[1] if container_image else None
                )
            except IndexError:
                image_digest = None

        # Get service account email from template.template.serviceAccount
        service_account_email = task_template.get("serviceAccount")

        transformed.append(
            {
                "id": full_name,
                "name": short_name,
                "location": location,
                "container_image": container_image,
                "image_digest": image_digest,
                # Cloud Run only supports x86_64 (amd64); ARM workloads are not supported
                "architecture": "amd64",
                "architecture_normalized": "amd64",
                "architecture_source": "platform_requirement",
                "service_account_email": service_account_email,
                "project_id": project_id,
                "labels": job.get("labels", {}),
            },
        )
    return transformed


@timeit
def load_jobs(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    """
    Loads GCPCloudRunJob nodes and their relationships.
    """
    load(
        neo4j_session,
        GCPCloudRunJobSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def cleanup_jobs(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """
    Cleans up stale Cloud Run jobs.
    """
    GraphJob.from_node_schema(GCPCloudRunJobSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_jobs(
    neo4j_session: neo4j.Session,
    client: Resource,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
    credentials: Optional[GoogleCredentials] = None,
) -> None:
    """
    Syncs GCP Cloud Run Jobs for a project.
    """
    logger.info(f"Syncing Cloud Run Jobs for project {project_id}.")
    jobs_raw = get_jobs(client, project_id, credentials=credentials)
    if not jobs_raw:
        logger.info(f"No Cloud Run jobs found for project {project_id}.")

    jobs = transform_jobs(jobs_raw, project_id)
    load_jobs(neo4j_session, jobs, project_id, update_tag)
    sync_labels(
        neo4j_session,
        jobs,
        "cloud_run_job",
        project_id,
        update_tag,
        common_job_parameters,
    )

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["project_id"] = project_id
    cleanup_jobs(neo4j_session, cleanup_job_params)
