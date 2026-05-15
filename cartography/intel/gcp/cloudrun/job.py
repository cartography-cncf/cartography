import logging
import re
from typing import Any

import neo4j
from google.auth.credentials import Credentials as GoogleCredentials

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.container_arch import ARCH_SOURCE_PLATFORM_REQUIREMENT
from cartography.intel.container_arch import normalize_architecture
from cartography.intel.container_image import parse_image_uri
from cartography.intel.gcp.clients import build_cloud_run_job_client
from cartography.intel.gcp.cloudrun.util import CLOUD_RUN_LABEL_BATCH_SIZE
from cartography.intel.gcp.cloudrun.util import fetch_cloud_run_resources_for_locations
from cartography.intel.gcp.cloudrun.util import list_cloud_run_resources_for_location
from cartography.intel.gcp.labels import sync_labels
from cartography.models.gcp.cloudrun.job import GCPCloudRunJobSchema
from cartography.models.gcp.cloudrun.job_container import GCPCloudRunJobContainerSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_jobs(
    project_id: str,
    locations: list[str],
    credentials: GoogleCredentials,
) -> list[dict]:
    """
    Get GCP Cloud Run Jobs for a project across cached locations.
    """

    client = build_cloud_run_job_client(credentials=credentials)

    def fetch_for_location(location: str) -> list[dict]:
        return list_cloud_run_resources_for_location(
            fetcher=lambda **kw: client.list_jobs(parent=location, **kw),
            resource_type="jobs",
            location=location,
            project_id=project_id,
        )

    return fetch_cloud_run_resources_for_locations(
        locations=locations,
        project_id=project_id,
        resource_type="jobs",
        fetch_for_location=fetch_for_location,
    )


def transform_jobs(jobs_data: list[dict], project_id: str) -> list[dict]:
    """
    Transform the list of Cloud Run Job dicts into job-level records (one per Job).
    """
    transformed: list[dict] = []
    for job in jobs_data:
        full_name = job["name"]
        name_match = re.match(
            r"projects/[^/]+/locations/([^/]+)/jobs/([^/]+)",
            full_name,
        )
        location = name_match.group(1) if name_match else None
        short_name = name_match.group(2) if name_match else None

        task_template = job.get("template", {}).get("template", {})
        service_account_email = task_template.get("serviceAccount")

        transformed.append(
            {
                "id": full_name,
                "name": short_name,
                "location": location,
                "service_account_email": service_account_email,
                "project_id": project_id,
                "labels": job.get("labels", {}),
            },
        )
    return transformed


def transform_containers(jobs_data: list[dict], project_id: str) -> list[dict]:
    """
    Flatten the Job -> template.template.containers[] into one record per individual container.
    Each container node represents a single container spec in the Job's task template.
    """
    transformed: list[dict[str, Any]] = []
    for job in jobs_data:
        job_id = job["name"]
        task_template = job.get("template", {}).get("template", {})
        containers = task_template.get("containers", []) or []

        for index, container in enumerate(containers):
            image, image_digest = parse_image_uri(container.get("image"))
            container_name = container.get("name") or str(index)
            transformed.append(
                {
                    "id": f"{job_id}/containers/{container_name}",
                    "name": container_name,
                    "job_id": job_id,
                    "image": image,
                    "image_digest": image_digest,
                    # Cloud Run only supports amd64; ARM is not supported.
                    "architecture": "amd64",
                    "architecture_normalized": normalize_architecture("amd64"),
                    "architecture_source": ARCH_SOURCE_PLATFORM_REQUIREMENT,
                    "project_id": project_id,
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
    load(
        neo4j_session,
        GCPCloudRunJobSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def load_containers(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPCloudRunJobContainerSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def cleanup_jobs(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    GraphJob.from_node_schema(GCPCloudRunJobSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def cleanup_containers(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    GraphJob.from_node_schema(
        GCPCloudRunJobContainerSchema(),
        common_job_parameters,
    ).run(
        neo4j_session,
    )


@timeit
def sync_jobs(
    neo4j_session: neo4j.Session,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
    cloud_run_locations: list[str],
    credentials: GoogleCredentials,
) -> None:
    """
    Sync GCP Cloud Run Jobs for a project.
    """
    logger.info("Syncing Cloud Run Jobs for project %s.", project_id)
    jobs_raw = get_jobs(project_id, cloud_run_locations, credentials)
    if not jobs_raw:
        logger.info("No Cloud Run jobs found for project %s.", project_id)

    jobs = transform_jobs(jobs_raw, project_id)
    load_jobs(neo4j_session, jobs, project_id, update_tag)

    containers = transform_containers(jobs_raw, project_id)
    load_containers(neo4j_session, containers, project_id, update_tag)

    sync_labels(
        neo4j_session,
        jobs,
        "cloud_run_job",
        project_id,
        update_tag,
        common_job_parameters,
        batch_size=CLOUD_RUN_LABEL_BATCH_SIZE,
    )

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["project_id"] = project_id
    cleanup_containers(neo4j_session, cleanup_job_params)
    cleanup_jobs(neo4j_session, cleanup_job_params)
