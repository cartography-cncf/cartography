import logging

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.cloudrun.service import GCPCloudRunServiceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_cloud_run_services(client: Resource, location_name: str) -> list[dict]:
    services: list[dict] = []
    request = client.projects().locations().services().list(parent=location_name)
    while request is not None:
        response = request.execute()
        services.extend(response.get("services", []))
        request = (
            client.projects()
            .locations()
            .services()
            .list_next(
                previous_request=request,
                previous_response=response,
            )
        )
    return services


def transform_services(services_data: list[dict], project_id: str) -> list[dict]:
    transformed: list[dict] = []
    for service in services_data:
        service_id = service.get("name")
        if not service_id:
            continue
        transformed.append(
            {
                "id": service_id,
                "name": service.get("name", "").split("/")[-1],
                "description": service.get("description"),
                "location": service.get("name", "").split("/")[3],
                "uri": service.get("uri"),
                "latest_ready_revision": service.get("latestReadyRevision"),
                "project_id": project_id,
            },
        )
    return transformed


@timeit
def load_cloud_run_services(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPCloudRunServiceSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def cleanup_cloud_run_services(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(GCPCloudRunServiceSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_cloud_run_services(
    neo4j_session: neo4j.Session,
    client: Resource,
    locations: list[dict],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> list[dict]:
    logger.info(f"Syncing Cloud Run Services for project {project_id}.")
    all_services_raw: list[dict] = []
    for loc in locations:
        location_id = loc.get("locationId")
        if not location_id:
            continue
        location_name = f"projects/{project_id}/locations/{location_id}"
        all_services_raw.extend(get_cloud_run_services(client, location_name))

    services = transform_services(all_services_raw, project_id)
    load_cloud_run_services(neo4j_session, services, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["project_id"] = project_id
    cleanup_cloud_run_services(neo4j_session, cleanup_job_params)

    return all_services_raw
