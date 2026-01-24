import logging
import re

import neo4j
from google.api_core.exceptions import PermissionDenied
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.cloudrun.revision import GCPCloudRunRevisionSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_revisions(client: Resource, project_id: str, location: str = "-") -> list[dict]:
    """
    Gets GCP Cloud Run Revisions for a project and location.
    """
    revisions: list[dict] = []
    try:
        # First, get all services so we can iterate through them to get revisions
        # The v2 API doesn't support double wildcards for location and service
        services_parent = f"projects/{project_id}/locations/{location}"
        services_request = (
            client.projects().locations().services().list(parent=services_parent)
        )

        while services_request is not None:
            services_response = services_request.execute()
            services = services_response.get("services", [])

            # For each service, get its revisions
            for service in services:
                service_name = service.get("name", "")
                revisions_request = (
                    client.projects()
                    .locations()
                    .services()
                    .revisions()
                    .list(parent=service_name)
                )

                while revisions_request is not None:
                    revisions_response = revisions_request.execute()
                    revisions.extend(revisions_response.get("revisions", []))
                    revisions_request = (
                        client.projects()
                        .locations()
                        .services()
                        .revisions()
                        .list_next(
                            previous_request=revisions_request,
                            previous_response=revisions_response,
                        )
                    )

            services_request = (
                client.projects()
                .locations()
                .services()
                .list_next(
                    previous_request=services_request,
                    previous_response=services_response,
                )
            )

        return revisions
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            f"Failed to get Cloud Run revisions for project {project_id} due to permissions or auth error: {e}",
        )
        raise


def transform_revisions(revisions_data: list[dict], project_id: str) -> list[dict]:
    """
    Transforms the list of Cloud Run Revision dicts for ingestion.
    """
    transformed: list[dict] = []
    for revision in revisions_data:
        # Full resource name: projects/{project}/locations/{location}/services/{service}/revisions/{revision}
        full_name = revision.get("name", "")

        # Extract location and short name from the full resource name
        name_match = re.match(
            r"projects/[^/]+/locations/([^/]+)/services/([^/]+)/revisions/([^/]+)",
            full_name,
        )
        location = name_match.group(1) if name_match else None
        short_name = name_match.group(3) if name_match else None

        # Get service short name from the v2 API response (it's just the short name, not full path)
        service_short_name = revision.get("service")

        # Construct the full service resource name for the relationship
        service_full_name = None
        if location and service_short_name:
            service_full_name = f"projects/{project_id}/locations/{location}/services/{service_short_name}"

        # Get container image from containers[0].image (v2 API has containers at top level)
        containers = revision.get("containers", [])
        container_image = None
        if containers:
            container_image = containers[0].get("image")

        # Get service account email (v2 API has serviceAccount at top level)
        service_account_email = revision.get("serviceAccount")

        # Get log URI directly from API response
        log_uri = revision.get("logUri")

        transformed.append(
            {
                "id": full_name,
                "name": short_name,
                "service": service_full_name,
                "container_image": container_image,
                "service_account_email": service_account_email,
                "log_uri": log_uri,
                "project_id": project_id,
            },
        )
    return transformed


@timeit
def load_revisions(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    """
    Loads GCPCloudRunRevision nodes and their relationships.
    """
    load(
        neo4j_session,
        GCPCloudRunRevisionSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def cleanup_revisions(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """
    Cleans up stale Cloud Run revisions.
    """
    GraphJob.from_node_schema(GCPCloudRunRevisionSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_revisions(
    neo4j_session: neo4j.Session,
    client: Resource,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Syncs GCP Cloud Run Revisions for a project.
    """
    logger.info(f"Syncing Cloud Run Revisions for project {project_id}.")
    revisions_raw = get_revisions(client, project_id)
    if not revisions_raw:
        logger.info(f"No Cloud Run revisions found for project {project_id}.")

    revisions = transform_revisions(revisions_raw, project_id)
    load_revisions(neo4j_session, revisions, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["project_id"] = project_id
    cleanup_revisions(neo4j_session, cleanup_job_params)
