import logging

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.cloudrun.job import GCPCloudRunJobSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_cloud_run_jobs(client: Resource, location_name: str) -> list[dict]:
    jobs: list[dict] = []
    request = client.projects().locations().jobs().list(parent=location_name)
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
    return jobs


def transform_jobs(jobs_data: list[dict], project_id: str) -> list[dict]:
    transformed: list[dict] = []
    for job in jobs_data:
        job_id = job.get("name")
        if not job_id:
            continue
        template = job.get("template", {}).get("template", {})
        containers = template.get("containers", [])
        container_image = containers[0].get("image") if containers else None
        transformed.append(
            {
                "id": job_id,
                "name": job.get("name", "").split("/")[-1],
                "location": job.get("name", "").split("/")[3],
                "container_image": container_image,
                "service_account_email": template.get("serviceAccount"),
                "project_id": project_id,
            },
        )
    return transformed


@timeit
def load_cloud_run_jobs(
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
def cleanup_cloud_run_jobs(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(GCPCloudRunJobSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_cloud_run_jobs(
    neo4j_session: neo4j.Session,
    client: Resource,
    locations: list[dict],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> list[dict]:
    logger.info(f"Syncing Cloud Run Jobs for project {project_id}.")
    all_jobs_raw: list[dict] = []
    for loc in locations:
        location_id = loc.get("locationId")
        if not location_id:
            continue
        location_name = f"projects/{project_id}/locations/{location_id}"
        all_jobs_raw.extend(get_cloud_run_jobs(client, location_name))

    jobs = transform_jobs(all_jobs_raw, project_id)
    load_cloud_run_jobs(neo4j_session, jobs, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["project_id"] = project_id
    cleanup_cloud_run_jobs(neo4j_session, cleanup_job_params)

    return all_jobs_raw
