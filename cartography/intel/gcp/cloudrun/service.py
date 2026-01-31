import logging
import re

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import is_api_disabled_error
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

        transformed.append(
            {
                "id": full_name,
                "name": short_name,
                "description": service.get("description"),
                "location": location,
                "uri": service.get("uri"),
                "latest_ready_revision": latest_ready_revision,
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

    # Only load and cleanup if we successfully retrieved data (even if empty list).
    # If get() returned None due to API not enabled, skip both to preserve existing data.
    if services_raw is not None:
        if not services_raw:
            logger.info(f"No Cloud Run services found for project {project_id}.")

        services = transform_services(services_raw, project_id)
        load_services(neo4j_session, services, project_id, update_tag)

        cleanup_job_params = common_job_parameters.copy()
        cleanup_job_params["project_id"] = project_id
        cleanup_services(neo4j_session, cleanup_job_params)
