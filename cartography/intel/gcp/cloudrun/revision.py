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

    :param client: The Cloud Run API client
    :param project_id: The GCP project ID
    :param location: The location to query. Use "-" to query all locations (default)
    :return: List of Cloud Run Revision dictionaries
    """
    revisions: list[dict] = []
    try:
        parent = f"projects/{project_id}/locations/{location}"
        request = client.revisions().list(parent=parent)
        while request is not None:
            response = request.execute()
            revisions.extend(response.get("revisions", []))
            request = client.revisions().list_next(
                previous_request=request,
                previous_response=response,
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

    :param revisions_data: Raw revision data from the Cloud Run API
    :param project_id: The GCP project ID
    :return: Transformed list of revision dictionaries
    """
    transformed: list[dict] = []
    for revision in revisions_data:
        # Full resource name: projects/{project}/locations/{location}/services/{service}/revisions/{revision}
        full_name = revision.get("name", "")

        # Extract location, service name, and short name from the full resource name
        name_match = re.match(
            r"projects/[^/]+/locations/([^/]+)/services/([^/]+)/revisions/([^/]+)",
            full_name,
        )
        location = name_match.group(1) if name_match else None
        service_short_name = name_match.group(2) if name_match else None
        short_name = name_match.group(3) if name_match else None

        # Construct the full service resource name
        service_full_name = None
        if location and service_short_name:
            service_full_name = f"projects/{project_id}/locations/{location}/services/{service_short_name}"

        # Get container image from template.containers[0].image
        container_image = None
        template = revision.get("template", {})
        containers = template.get("containers", [])
        if containers and len(containers) > 0:
            container_image = containers[0].get("image")

        # Get service account email from template.serviceAccount
        service_account_email = template.get("serviceAccount")

        # Construct log URI - Cloud Console logs viewer URL
        log_uri = None
        if location:
            log_uri = (
                f"https://console.cloud.google.com/run/detail/{location}/"
                f"{service_short_name}/revisions/{short_name}/logs?project={project_id}"
            )

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

    :param neo4j_session: The Neo4j session
    :param data: Transformed revision data
    :param project_id: The GCP project ID
    :param update_tag: Timestamp for tracking updates
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

    :param neo4j_session: The Neo4j session
    :param common_job_parameters: Common job parameters for cleanup
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

    :param neo4j_session: The Neo4j session
    :param client: The Cloud Run API client
    :param project_id: The GCP project ID
    :param update_tag: Timestamp for tracking updates
    :param common_job_parameters: Common job parameters for cleanup
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
