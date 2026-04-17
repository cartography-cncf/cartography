import logging
import re
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.container_arch import ARCH_SOURCE_PLATFORM_REQUIREMENT
from cartography.intel.container_arch import normalize_architecture
from cartography.intel.gcp.cloudrun.util import extract_container_image_metadata
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import is_api_disabled_error
from cartography.models.gcp.cloudrun.revision import GCPCloudRunRevisionSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_DEFAULT_CLOUD_RUN_REVISION_WORKERS = 10


def _get_revisions_for_service(client: Resource, service_name: str) -> list[dict]:
    revisions: list[dict] = []
    revisions_request = (
        client.projects().locations().services().revisions().list(parent=service_name)
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

    return revisions


@timeit
def get_revisions(
    client: Resource,
    project_id: str,
    location: str = "-",
    services_raw: list[dict] | None = None,
    max_workers: int = _DEFAULT_CLOUD_RUN_REVISION_WORKERS,
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
        if services_raw is None:
            services_parent = f"projects/{project_id}/locations/{location}"
            services_request = (
                client.projects().locations().services().list(parent=services_parent)
            )
            services_raw = []
            while services_request is not None:
                services_response = gcp_api_execute_with_retry(services_request)
                services_raw.extend(services_response.get("services", []))
                services_request = (
                    client.projects()
                    .locations()
                    .services()
                    .list_next(
                        previous_request=services_request,
                        previous_response=services_response,
                    )
                )

        service_names = [
            service.get("name", "") for service in services_raw if service.get("name")
        ]
        if not service_names:
            return []

        revisions: list[dict] = []
        with ThreadPoolExecutor(
            max_workers=min(max_workers, len(service_names)),
        ) as executor:
            futures = {
                executor.submit(
                    _get_revisions_for_service, client, service_name
                ): service_name
                for service_name in service_names
            }
            for future in as_completed(futures):
                revisions.extend(future.result())

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

        containers = revision.get("containers", [])
        image_metadata = extract_container_image_metadata(containers)

        # Get service account email (v2 API has serviceAccount at top level)
        service_account_email = revision.get("serviceAccount")

        # Get log URI directly from API response
        log_uri = revision.get("logUri")

        transformed.append(
            {
                "id": full_name,
                "name": short_name,
                "service": service_full_name,
                "container_image": image_metadata["container_image"],
                "container_images": image_metadata["container_images"],
                "image_digest": image_metadata["image_digest"],
                "image_digests": image_metadata["image_digests"],
                # Cloud Run only supports x86_64 (amd64); ARM workloads are not supported
                "architecture": "amd64",
                "architecture_normalized": normalize_architecture("amd64"),
                "architecture_source": ARCH_SOURCE_PLATFORM_REQUIREMENT,
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
    services_raw: list[dict] | None = None,
) -> None:
    """
    Syncs GCP Cloud Run Revisions for a project.
    """
    logger.info(f"Syncing Cloud Run Revisions for project {project_id}.")
    revisions_raw = get_revisions(
        client,
        project_id,
        services_raw=services_raw,
    )

    if revisions_raw is not None:
        if not revisions_raw:
            logger.info(f"No Cloud Run revisions found for project {project_id}.")

        revisions = transform_revisions(revisions_raw, project_id)
        load_revisions(neo4j_session, revisions, project_id, update_tag)

        cleanup_job_params = common_job_parameters.copy()
        cleanup_job_params["project_id"] = project_id
        cleanup_revisions(neo4j_session, cleanup_job_params)
