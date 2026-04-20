import logging
import re
from collections.abc import Iterable
from typing import Optional

import neo4j
from google.api_core.exceptions import PermissionDenied
from google.auth.credentials import Credentials as GoogleCredentials
from google.cloud.run_v2 import JobsClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.container_arch import ARCH_SOURCE_PLATFORM_REQUIREMENT
from cartography.intel.container_arch import normalize_architecture
from cartography.intel.gcp.cloudrun.util import discover_cloud_run_locations
from cartography.intel.gcp.cloudrun.util import extract_container_image_metadata
from cartography.intel.gcp.labels import sync_labels
from cartography.intel.gcp.util import proto_message_to_dict
from cartography.models.gcp.cloudrun.job import GCPCloudRunJobSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_jobs(
    client: JobsClient,
    project_id: str,
    location: str = "-",
    credentials: Optional[GoogleCredentials] = None,
    locations: Iterable[str] | None = None,
) -> list[dict] | None:
    """
    Gets GCP Cloud Run Jobs for a project and location.
    """
    jobs: list[dict] = []
    location_names: set[str]

    if locations is not None:
        location_names = set(locations)
    elif location == "-":
        discovered_locations = discover_cloud_run_locations(
            project_id,
            credentials=credentials,
        )
        if discovered_locations is None:
            return None
        location_names = discovered_locations
    else:
        location_names = {f"projects/{project_id}/locations/{location}"}

    queried_any_location = False
    had_permission_denied = False

    for loc_name in sorted(location_names):
        try:
            pager = client.list_jobs(parent=loc_name)
            location_jobs = [proto_message_to_dict(job) for job in pager]
            jobs.extend(location_jobs)
            queried_any_location = True
        except PermissionDenied:
            had_permission_denied = True
            logger.warning(
                "Permission denied listing Cloud Run jobs in %s. Skipping location.",
                loc_name,
            )
            continue

    if had_permission_denied and not queried_any_location:
        logger.warning(
            "Could not retrieve Cloud Run jobs on project %s due to permissions issues. "
            "Skipping sync to preserve existing data.",
            project_id,
        )
        return None

    return jobs


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

        template = job.get("template", {})
        task_template = template.get("template", {})
        containers = task_template.get("containers", [])
        image_metadata = extract_container_image_metadata(containers)

        # Get service account email from template.template.serviceAccount
        service_account_email = task_template.get("serviceAccount")

        transformed.append(
            {
                "id": full_name,
                "name": short_name,
                "location": location,
                "container_image": image_metadata["container_image"],
                "container_images": image_metadata["container_images"],
                "image_digest": image_metadata["image_digest"],
                "image_digests": image_metadata["image_digests"],
                # Cloud Run only supports x86_64 (amd64); ARM workloads are not supported
                "architecture": "amd64",
                "architecture_normalized": normalize_architecture("amd64"),
                "architecture_source": ARCH_SOURCE_PLATFORM_REQUIREMENT,
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
    client: JobsClient,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
    credentials: Optional[GoogleCredentials] = None,
    locations: Iterable[str] | None = None,
    jobs_raw: list[dict] | None = None,
) -> list[dict] | None:
    """
    Syncs GCP Cloud Run Jobs for a project.
    """
    logger.info(f"Syncing Cloud Run Jobs for project {project_id}.")
    if jobs_raw is None:
        jobs_raw = get_jobs(
            client,
            project_id,
            credentials=credentials,
            locations=locations,
        )

    if jobs_raw is not None:
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

    return jobs_raw
