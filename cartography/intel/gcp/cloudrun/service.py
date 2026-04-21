import logging
import re
from typing import Any

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.container_arch import ARCH_SOURCE_PLATFORM_REQUIREMENT
from cartography.intel.container_arch import normalize_architecture
from cartography.intel.container_image import parse_image_uri
from cartography.intel.gcp.labels import sync_labels
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import is_api_disabled_error
from cartography.models.gcp.cloudrun.container import GCPCloudRunContainerSchema
from cartography.models.gcp.cloudrun.service import GCPCloudRunServiceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_services(
    client: Resource, project_id: str, location: str = "-"
) -> list[dict] | None:
    """
    Gets GCP Cloud Run Services for a project and location.

    Returns:
        list[dict]: List of Cloud Run services (empty list if project has no services)
        None: If the Cloud Run Admin API is not enabled or access is denied

    Raises:
        HttpError: For errors other than API disabled or permission denied
    """
    try:
        services: list[dict] = []
        parent = f"projects/{project_id}/locations/{location}"
        request = client.projects().locations().services().list(parent=parent)
        while request is not None:
            response = gcp_api_execute_with_retry(request)
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
    except HttpError as e:
        if is_api_disabled_error(e):
            logger.warning(
                "Could not retrieve Cloud Run services on project %s due to permissions "
                "issues or API not enabled. Skipping sync to preserve existing data.",
                project_id,
            )
            return None
        raise


def transform_services(services_data: list[dict], project_id: str) -> list[dict]:
    """
    Transforms the list of Cloud Run Service dicts into service-level records.
    """
    transformed: list[dict] = []
    for service in services_data:
        full_name = service.get("name", "")

        name_match = re.match(
            r"projects/[^/]+/locations/([^/]+)/services/([^/]+)",
            full_name,
        )
        location = name_match.group(1) if name_match else None
        short_name = name_match.group(2) if name_match else None

        latest_ready_revision = service.get("latestReadyRevision")
        service_account_email = service.get("template", {}).get("serviceAccount")

        transformed.append(
            {
                "id": full_name,
                "name": short_name,
                "description": service.get("description"),
                "location": location,
                "uri": service.get("uri"),
                "latest_ready_revision": latest_ready_revision,
                "service_account_email": service_account_email,
                "ingress": service.get("ingress"),
                "project_id": project_id,
                "labels": service.get("labels", {}),
            },
        )
    return transformed


def transform_containers(services_data: list[dict], project_id: str) -> list[dict]:
    """
    Flattens service.template.containers[] into one record per individual container.
    The Cloud Run v2 API returns the latestReadyRevision's spec inline as service.template,
    so this captures the current canonical container set per service.
    """
    transformed: list[dict[str, Any]] = []
    for service in services_data:
        service_id = service.get("name", "")
        template = service.get("template") or {}
        containers = template.get("containers", []) or []

        for index, container in enumerate(containers):
            image, image_digest = parse_image_uri(container.get("image"))
            container_name = container.get("name") or str(index)
            transformed.append(
                {
                    "id": f"{service_id}/containers/{container_name}",
                    "name": container_name,
                    "job_id": None,
                    "service_id": service_id,
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
def load_services(
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
def load_containers(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPCloudRunContainerSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def cleanup_services(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    GraphJob.from_node_schema(GCPCloudRunServiceSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_services(
    neo4j_session: neo4j.Session,
    client: Resource,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Syncs GCP Cloud Run Services for a project.
    """
    logger.info(f"Syncing Cloud Run Services for project {project_id}.")
    services_raw = get_services(client, project_id)

    if services_raw is not None:
        if not services_raw:
            logger.info(f"No Cloud Run services found for project {project_id}.")

        services = transform_services(services_raw, project_id)
        load_services(neo4j_session, services, project_id, update_tag)

        containers = transform_containers(services_raw, project_id)
        load_containers(neo4j_session, containers, project_id, update_tag)

        sync_labels(
            neo4j_session,
            services,
            "cloud_run_service",
            project_id,
            update_tag,
            common_job_parameters,
        )

        cleanup_job_params = common_job_parameters.copy()
        cleanup_job_params["project_id"] = project_id
        cleanup_services(neo4j_session, cleanup_job_params)
