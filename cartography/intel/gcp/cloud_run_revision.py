import logging

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.cloudrun.revision import GCPCloudRunRevisionSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_cloud_run_revisions(client: Resource, service_name: str) -> list[dict]:
    revisions: list[dict] = []
    request = (
        client.projects().locations().services().revisions().list(parent=service_name)
    )
    while request is not None:
        response = request.execute()
        revisions.extend(response.get("revisions", []))
        request = (
            client.projects()
            .locations()
            .services()
            .revisions()
            .list_next(
                previous_request=request,
                previous_response=response,
            )
        )
    return revisions


def transform_revisions(revisions_data: list[dict], project_id: str) -> list[dict]:
    transformed: list[dict] = []
    for rev in revisions_data:
        rev_id = rev.get("name")
        if not rev_id:
            raise ValueError(
                "Cloud Run revision is missing the required 'name' field from the API response"
            )
        containers = rev.get("containers", [])
        container_image = containers[0].get("image") if containers else None
        transformed.append(
            {
                "id": rev_id,
                "name": rev.get("name", "").split("/")[-1],
                "service": rev.get("name", "").rsplit("/revisions/", 1)[0],
                "container_image": container_image,
                "service_account_email": rev.get("serviceAccount"),
                "log_uri": rev.get("logUri"),
                "project_id": project_id,
            },
        )
    return transformed


@timeit
def load_cloud_run_revisions(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPCloudRunRevisionSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def cleanup_cloud_run_revisions(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(GCPCloudRunRevisionSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_cloud_run_revisions(
    neo4j_session: neo4j.Session,
    client: Resource,
    services_raw: list[dict],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(f"Syncing Cloud Run Revisions for project {project_id}.")
    all_revisions: list[dict] = []
    for svc_raw in services_raw:
        service_name = svc_raw.get("name")
        if not service_name:
            raise ValueError(
                "Cloud Run service is missing the required name from the API response"
            )
        revisions_raw = get_cloud_run_revisions(client, service_name)
        all_revisions.extend(transform_revisions(revisions_raw, project_id))

    load_cloud_run_revisions(neo4j_session, all_revisions, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["project_id"] = project_id
    cleanup_cloud_run_revisions(neo4j_session, cleanup_job_params)
