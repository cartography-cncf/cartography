import logging
from typing import Any

import neo4j
from google.api_core.exceptions import PermissionDenied
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.cloudrun.domain_mapping import (
    GCPCloudRunDomainMappingSchema,
)
from cartography.models.gcp.cloudrun.execution import GCPCloudRunExecutionSchema
from cartography.models.gcp.cloudrun.job import GCPCloudRunJobSchema
from cartography.models.gcp.cloudrun.revision import GCPCloudRunRevisionSchema
from cartography.models.gcp.cloudrun.service import GCPCloudRunServiceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_cloud_run_locations(client: Resource, project_id: str) -> list[dict]:
    locations: list[dict] = []
    try:
        parent = f"projects/{project_id}"
        request = client.projects().locations().list(name=parent)

        while request is not None:
            response = request.execute()
            locations.extend(response.get("locations", []))
            request = (
                client.projects()
                .locations()
                .list_next(
                    previous_request=request,
                    previous_response=response,
                )
            )
        return locations
    except (PermissionDenied, DefaultCredentialsError, RefreshError):
        logger.warning(
            "Failed to get Cloud Run locations due to permissions or auth error.",
            exc_info=True,
        )
        raise
    except HttpError:
        logger.warning(
            "Failed to get Cloud Run locations due to a transient HTTP error.",
            exc_info=True,
        )
        return []


@timeit
def get_cloud_run_services(client: Resource, location_name: str) -> list[dict]:
    services: list[dict] = []
    try:
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
    except (PermissionDenied, DefaultCredentialsError, RefreshError):
        logger.warning(
            "Failed to get Cloud Run services due to permissions or auth error.",
            exc_info=True,
        )
        raise
    except HttpError:
        logger.warning(
            "Failed to get Cloud Run services due to a transient HTTP error.",
            exc_info=True,
        )
        return []


@timeit
def get_cloud_run_revisions(client: Resource, service_name: str) -> list[dict]:
    revisions: list[dict] = []
    try:
        request = (
            client.projects()
            .locations()
            .services()
            .revisions()
            .list(parent=service_name)
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
    except (PermissionDenied, DefaultCredentialsError, RefreshError):
        logger.warning(
            "Failed to get Cloud Run revisions due to permissions or auth error.",
            exc_info=True,
        )
        raise
    except HttpError:
        logger.warning(
            "Failed to get Cloud Run revisions due to a transient HTTP error.",
            exc_info=True,
        )
        return []


@timeit
def get_cloud_run_jobs(client: Resource, location_name: str) -> list[dict]:
    jobs: list[dict] = []
    try:
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
    except (PermissionDenied, DefaultCredentialsError, RefreshError):
        logger.warning(
            "Failed to get Cloud Run jobs due to permissions or auth error.",
            exc_info=True,
        )
        raise
    except HttpError:
        logger.warning(
            "Failed to get Cloud Run jobs due to a transient HTTP error.",
            exc_info=True,
        )
        return []


@timeit
def get_cloud_run_executions(client: Resource, job_name: str) -> list[dict]:
    executions: list[dict] = []
    try:
        request = (
            client.projects().locations().jobs().executions().list(parent=job_name)
        )
        while request is not None:
            response = request.execute()
            executions.extend(response.get("executions", []))
            request = (
                client.projects()
                .locations()
                .jobs()
                .executions()
                .list_next(
                    previous_request=request,
                    previous_response=response,
                )
            )
        return executions
    except (PermissionDenied, DefaultCredentialsError, RefreshError):
        logger.warning(
            "Failed to get Cloud Run executions due to permissions or auth error.",
            exc_info=True,
        )
        raise
    except HttpError:
        logger.warning(
            "Failed to get Cloud Run executions due to a transient HTTP error.",
            exc_info=True,
        )
        return []


@timeit
def get_cloud_run_domain_mappings(client: Resource, location_name: str) -> list[dict]:
    mappings: list[dict] = []
    try:
        request = (
            client.projects().locations().domainmappings().list(parent=location_name)
        )
        response = request.execute()
        mappings.extend(response.get("domainMappings", []))
        return mappings
    except (PermissionDenied, DefaultCredentialsError, RefreshError):
        logger.warning(
            "Failed to get Cloud Run domain mappings due to permissions or auth error.",
            exc_info=True,
        )
        raise
    except HttpError:
        logger.warning(
            "Failed to get Cloud Run domain mappings due to a transient HTTP error.",
            exc_info=True,
        )
        return []


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
            }
        )
    return transformed


def transform_revisions(revisions_data: list[dict], project_id: str) -> list[dict]:
    transformed: list[dict] = []
    for rev in revisions_data:
        rev_id = rev.get("name")
        if not rev_id:
            continue

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
            }
        )
    return transformed


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
            }
        )
    return transformed


def transform_executions(executions_data: list[dict], project_id: str) -> list[dict]:
    transformed: list[dict] = []
    for ex in executions_data:
        ex_id = ex.get("name")
        if not ex_id:
            continue
        status_data = ex.get("status", {})

        transformed.append(
            {
                "id": ex_id,
                "name": ex.get("name", "").split("/")[-1],
                "job": ex.get("name", "").rsplit("/executions/", 1)[0],
                "status": str(status_data.get("completionTime", "RUNNING")),
                "cancelled_count": ex.get("cancelledCount"),
                "failed_count": ex.get("failedCount"),
                "succeeded_count": ex.get("succeededCount"),
                "project_id": project_id,
            }
        )
    return transformed


def transform_domain_mappings(mappings_data: list[dict], project_id: str) -> list[dict]:
    transformed: list[dict] = []
    for mapping in mappings_data:
        mapping_id = mapping.get("name")
        if not mapping_id:
            continue

        transformed.append(
            {
                "id": mapping_id,
                "name": mapping_id.split("/")[-1],
                "route_name": mapping.get("spec", {}).get("routeName"),
                "project_id": project_id,
            }
        )
    return transformed


@timeit
def load_cloud_run_services(
    neo4j_session: neo4j.Session, data: list[dict], project_id: str, update_tag: int
) -> None:
    load(
        neo4j_session,
        GCPCloudRunServiceSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def load_cloud_run_revisions(
    neo4j_session: neo4j.Session, data: list[dict], project_id: str, update_tag: int
) -> None:
    load(
        neo4j_session,
        GCPCloudRunRevisionSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def load_cloud_run_jobs(
    neo4j_session: neo4j.Session, data: list[dict], project_id: str, update_tag: int
) -> None:
    load(
        neo4j_session,
        GCPCloudRunJobSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def load_cloud_run_executions(
    neo4j_session: neo4j.Session, data: list[dict], project_id: str, update_tag: int
) -> None:
    load(
        neo4j_session,
        GCPCloudRunExecutionSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def load_cloud_run_domain_mappings(
    neo4j_session: neo4j.Session, data: list[dict], project_id: str, update_tag: int
) -> None:
    load(
        neo4j_session,
        GCPCloudRunDomainMappingSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def cleanup_cloud_run(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(GCPCloudRunExecutionSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(GCPCloudRunRevisionSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(
        GCPCloudRunDomainMappingSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(GCPCloudRunJobSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(GCPCloudRunServiceSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    run_client: Resource,
    run_client_v1: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info(f"Syncing GCP Cloud Run for project {project_id}.")

    locations = get_cloud_run_locations(run_client_v1, project_id)
    if not locations:
        logger.info(f"No Cloud Run locations found for project {project_id}.")
        cleanup_job_params = common_job_parameters.copy()
        cleanup_job_params["project_id"] = project_id
        cleanup_cloud_run(neo4j_session, cleanup_job_params)
        return

    all_services_raw: list[dict] = []
    all_jobs_raw: list[dict] = []
    all_domain_mappings_raw: list[dict] = []

    for loc in locations:
        location_id = loc.get("locationId")
        if not location_id:
            continue
        location_name = f"projects/{project_id}/locations/{location_id}"

        all_services_raw.extend(get_cloud_run_services(run_client, location_name))
        all_jobs_raw.extend(get_cloud_run_jobs(run_client, location_name))
        all_domain_mappings_raw.extend(
            get_cloud_run_domain_mappings(run_client_v1, location_name)
        )

    services = transform_services(all_services_raw, project_id)
    jobs = transform_jobs(all_jobs_raw, project_id)
    domain_mappings = transform_domain_mappings(all_domain_mappings_raw, project_id)

    load_cloud_run_services(neo4j_session, services, project_id, gcp_update_tag)
    load_cloud_run_jobs(neo4j_session, jobs, project_id, gcp_update_tag)
    load_cloud_run_domain_mappings(
        neo4j_session, domain_mappings, project_id, gcp_update_tag
    )

    all_revisions: list[dict] = []
    for svc_raw in all_services_raw:
        service_name = svc_raw.get("name")
        if not service_name:
            continue
        revisions_raw = get_cloud_run_revisions(run_client, service_name)
        all_revisions.extend(transform_revisions(revisions_raw, project_id))

    load_cloud_run_revisions(neo4j_session, all_revisions, project_id, gcp_update_tag)

    all_executions: list[dict] = []
    for job_raw in all_jobs_raw:
        job_name = job_raw.get("name")
        if not job_name:
            continue
        executions_raw = get_cloud_run_executions(run_client, job_name)
        all_executions.extend(transform_executions(executions_raw, project_id))

    load_cloud_run_executions(neo4j_session, all_executions, project_id, gcp_update_tag)
    # TODO: Ingest traffic splitting (DIRECTS_TRAFFIC_TO)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["project_id"] = project_id
    cleanup_cloud_run(neo4j_session, cleanup_job_params)
