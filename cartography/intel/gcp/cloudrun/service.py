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
from cartography.intel.gcp.clients import build_cloud_run_service_client
from cartography.intel.gcp.cloudrun.util import CLOUD_RUN_LABEL_BATCH_SIZE
from cartography.intel.gcp.cloudrun.util import fetch_cloud_run_resources_for_locations
from cartography.intel.gcp.cloudrun.util import list_cloud_run_resources_for_location
from cartography.intel.gcp.labels import sync_labels
from cartography.models.gcp.cloudrun.service import GCPCloudRunServiceSchema
from cartography.models.gcp.cloudrun.service_container import (
    GCPCloudRunServiceContainerSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_services(
    project_id: str,
    locations: list[str],
    credentials: GoogleCredentials,
) -> list[dict]:
    """
    Get GCP Cloud Run Services for a project across cached locations.
    """

    client = build_cloud_run_service_client(credentials=credentials)

    def fetch_for_location(location: str) -> list[dict]:
        return list_cloud_run_resources_for_location(
            fetcher=lambda **kw: client.list_services(parent=location, **kw),
            resource_type="services",
            location=location,
            project_id=project_id,
        )

    return fetch_cloud_run_resources_for_locations(
        locations=locations,
        project_id=project_id,
        resource_type="services",
        fetch_for_location=fetch_for_location,
    )


def transform_services(services_data: list[dict], project_id: str) -> list[dict]:
    """
    Transform the list of Cloud Run Service dicts into service-level records.
    """
    transformed: list[dict] = []
    for service in services_data:
        full_name = service["name"]

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
    Flatten service.template.containers[] into one record per individual container.
    The Cloud Run v2 API returns the latestReadyRevision's spec inline as service.template,
    so this captures the current canonical container set per service.
    """
    transformed: list[dict[str, Any]] = []
    for service in services_data:
        service_id = service["name"]
        template = service.get("template") or {}
        containers = template.get("containers", []) or []

        for index, container in enumerate(containers):
            image, image_digest = parse_image_uri(container.get("image"))
            container_name = container.get("name") or str(index)
            transformed.append(
                {
                    "id": f"{service_id}/containers/{container_name}",
                    "name": container_name,
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
        GCPCloudRunServiceContainerSchema(),
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
def cleanup_containers(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    GraphJob.from_node_schema(
        GCPCloudRunServiceContainerSchema(),
        common_job_parameters,
    ).run(
        neo4j_session,
    )


@timeit
def sync_services(
    neo4j_session: neo4j.Session,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
    cloud_run_locations: list[str],
    credentials: GoogleCredentials,
) -> None:
    """
    Sync GCP Cloud Run Services for a project.
    """
    logger.info("Syncing Cloud Run Services for project %s.", project_id)
    services_raw = get_services(project_id, cloud_run_locations, credentials)
    if not services_raw:
        logger.info("No Cloud Run services found for project %s.", project_id)

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
        batch_size=CLOUD_RUN_LABEL_BATCH_SIZE,
    )

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["project_id"] = project_id
    cleanup_containers(neo4j_session, cleanup_job_params)
    cleanup_services(neo4j_session, cleanup_job_params)
