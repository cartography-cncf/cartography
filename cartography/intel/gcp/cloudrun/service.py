import logging
import re
from collections.abc import Iterable

import neo4j
from google.api_core.exceptions import PermissionDenied
from google.cloud.run_v2 import ServicesClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.labels import sync_labels
from cartography.intel.gcp.util import proto_message_to_dict
from cartography.models.gcp.cloudrun.service import GCPCloudRunServiceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_services(
    client: ServicesClient,
    project_id: str,
    locations: Iterable[str] | None = None,
) -> list[dict] | None:
    """
    Gets GCP Cloud Run Services for a project and location.

    Returns:
        list[dict]: List of Cloud Run services (empty list if project has no services)
        None: If the Cloud Run Admin API is not enabled or access is denied
    """
    services: list[dict] = []
    queried_any_location = False
    had_permission_denied = False

    for location in sorted(locations or []):
        try:
            pager = client.list_services(parent=location)
            location_services = [proto_message_to_dict(service) for service in pager]
            services.extend(location_services)
            queried_any_location = True
        except PermissionDenied:
            had_permission_denied = True
            logger.warning(
                "Permission denied listing Cloud Run services in %s. Skipping location.",
                location,
            )
            continue

    if had_permission_denied and not queried_any_location:
        logger.warning(
            "Could not retrieve Cloud Run services on project %s due to permissions "
            "issues. Skipping sync to preserve existing data.",
            project_id,
        )
        return None

    return services


def transform_services(services_data: list[dict], project_id: str) -> list[dict]:
    """
    Transforms the list of Cloud Run Service dicts for ingestion.
    """
    transformed: list[dict] = []
    for service in services_data:
        # Full resource name: projects/{project}/locations/{location}/services/{service}
        full_name = service.get("name", "")

        # Extract location and short name from the full resource name
        name_match = re.match(
            r"projects/[^/]+/locations/([^/]+)/services/([^/]+)",
            full_name,
        )
        location = name_match.group(1) if name_match else None
        short_name = name_match.group(2) if name_match else None

        # Get latest ready revision - the v2 API returns the full resource name
        latest_ready_revision = service.get("latestReadyRevision")

        # Get service account email from template.serviceAccount (v2 API)
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


@timeit
def load_services(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    """
    Loads GCPCloudRunService nodes and their relationships.
    """
    load(
        neo4j_session,
        GCPCloudRunServiceSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def cleanup_services(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """
    Cleans up stale Cloud Run services.
    """
    GraphJob.from_node_schema(GCPCloudRunServiceSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_services(
    neo4j_session: neo4j.Session,
    client: ServicesClient,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
    locations: Iterable[str] | None = None,
    services_raw: list[dict] | None = None,
) -> list[dict] | None:
    """
    Syncs GCP Cloud Run Services for a project.
    """
    logger.info(f"Syncing Cloud Run Services for project {project_id}.")
    if services_raw is None:
        services_raw = get_services(client, project_id, locations=locations)

    # Only load and cleanup if we successfully retrieved data (even if empty list).
    # If get() returned None due to API not enabled, skip both to preserve existing data.
    if services_raw is not None:
        if not services_raw:
            logger.info(f"No Cloud Run services found for project {project_id}.")

        services = transform_services(services_raw, project_id)
        load_services(neo4j_session, services, project_id, update_tag)
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

    return services_raw
