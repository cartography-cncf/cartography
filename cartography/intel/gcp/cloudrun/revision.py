import logging
import re

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import is_api_disabled_error
from cartography.models.gcp.cloudrun.revision import GCPCloudRunRevisionSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_revisions(
    client: Resource, project_id: str, location: str = "-"
) -> list[dict] | None:
    """
    Gets GCP Cloud Run Revisions for a project and location.

    Returns:
        list[dict]: List of Cloud Run revisions (empty list if project has no revisions)
        None: If the Cloud Run Admin API is not enabled or access is denied

    Raises:
        HttpError: For errors other than API disabled or permission denied
    """
    try:
        revisions: list[dict] = []
        services_parent = f"projects/{project_id}/locations/{location}"
        services_request = (
            client.projects().locations().services().list(parent=services_parent)
        )

        while services_request is not None:
            services_response = gcp_api_execute_with_retry(services_request)
            services = services_response.get("services", [])

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
                    revisions_response = gcp_api_execute_with_retry(revisions_request)
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
    except HttpError as e:
        if is_api_disabled_error(e):
            logger.warning(
                "Could not retrieve Cloud Run revisions on project %s due to permissions "
                "issues or API not enabled. Skipping sync to preserve existing data.",
                project_id,
            )
            return None
        raise


def transform_revisions(revisions_data: list[dict], project_id: str) -> list[dict]:
    """
    Transforms the list of Cloud Run Revision dicts into revision-level records.
    Revisions are pure versioning markers; per-container image data lives on the
    parent Service's GCPCloudRunContainer children (latestReadyRevision).
    """
    transformed: list[dict] = []
    for revision in revisions_data:
        full_name = revision["name"]

        name_match = re.match(
            r"projects/[^/]+/locations/([^/]+)/services/([^/]+)/revisions/([^/]+)",
            full_name,
        )
        location = name_match.group(1) if name_match else None
        short_name = name_match.group(3) if name_match else None

        service_short_name = revision.get("service")
        service_full_name = None
        if location and service_short_name:
            service_full_name = f"projects/{project_id}/locations/{location}/services/{service_short_name}"

        transformed.append(
            {
                "id": full_name,
                "name": short_name,
                "service": service_full_name,
                "service_account_email": revision.get("serviceAccount"),
                "log_uri": revision.get("logUri"),
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

    if revisions_raw is not None:
        if not revisions_raw:
            logger.info(f"No Cloud Run revisions found for project {project_id}.")

        revisions = transform_revisions(revisions_raw, project_id)
        load_revisions(neo4j_session, revisions, project_id, update_tag)

        cleanup_job_params = common_job_parameters.copy()
        cleanup_job_params["project_id"] = project_id
        cleanup_revisions(neo4j_session, cleanup_job_params)
