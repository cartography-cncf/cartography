"""
Utility functions for GCP Cloud Run intel modules.
"""

import logging
from collections.abc import Callable
from collections.abc import Iterable
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor

from google.api_core.exceptions import DeadlineExceeded
from google.api_core.exceptions import GoogleAPICallError
from google.api_core.exceptions import NotFound
from google.api_core.exceptions import PermissionDenied
from google.api_core.exceptions import ResourceExhausted
from google.api_core.exceptions import ServiceUnavailable
from google.api_core.retry import if_exception_type
from google.api_core.retry import Retry
from google.auth.credentials import Credentials as GoogleCredentials
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.intel.gcp.clients import build_client
from cartography.intel.gcp.clients import get_gcp_credentials
from cartography.intel.gcp.util import is_api_disabled_error
from cartography.intel.gcp.util import proto_message_to_dict
from cartography.util import timeit

logger = logging.getLogger(__name__)

CLOUD_RUN_LABEL_BATCH_SIZE = 1000
DEFAULT_CLOUD_RUN_LOCATION_WORKERS = 8
CLOUD_RUN_LIST_RETRY_INITIAL = 1.0
CLOUD_RUN_LIST_RETRY_MAX = 10.0
CLOUD_RUN_LIST_RETRY_MULTIPLIER = 1.3
CLOUD_RUN_LIST_RETRY_TIMEOUT = 60.0
CLOUD_RUN_LIST_TIMEOUT = 30.0


def _normalize_cloud_run_location_name(location_name: str) -> str:
    if location_name.startswith("projects/"):
        return location_name
    return f"projects/{location_name}"


def _cloud_run_location_short_name(location_name: str) -> str:
    return location_name.rsplit("/", 1)[-1]


def build_cloud_run_resource_retry(
    *,
    resource_type: str,
    location: str,
    project_id: str,
) -> Retry:
    location_short = _cloud_run_location_short_name(location)

    def _on_error(exc: Exception) -> None:
        logger.warning(
            "Retrying Cloud Run %s list in %s for project %s after transient error: %s",
            resource_type,
            location_short,
            project_id,
            exc,
        )

    return Retry(
        predicate=if_exception_type(
            DeadlineExceeded,
            ResourceExhausted,
            ServiceUnavailable,
        ),
        initial=CLOUD_RUN_LIST_RETRY_INITIAL,
        maximum=CLOUD_RUN_LIST_RETRY_MAX,
        multiplier=CLOUD_RUN_LIST_RETRY_MULTIPLIER,
        timeout=CLOUD_RUN_LIST_RETRY_TIMEOUT,
        on_error=_on_error,
    )


def _service_discovered_cloud_run_locations(
    client: Resource,
    project_id: str,
) -> list[str] | None:
    logger.debug(
        "Using service-based fallback discovery for Cloud Run locations in project %s.",
        project_id,
    )
    services_parent = f"projects/{project_id}/locations/-"
    services_request = (
        client.projects().locations().services().list(parent=services_parent)
    )

    discovered_locations: set[str] = set()
    while services_request is not None:
        try:
            services_response = services_request.execute()
        except HttpError as e:
            if is_api_disabled_error(e) or e.resp.status == 403:
                logger.warning(
                    "Could not retrieve Cloud Run locations on project %s due to permissions issues or API not enabled. "
                    "Skipping sync to preserve existing data.",
                    project_id,
                )
                return None
            raise

        for service in services_response.get("services", []):
            service_name = service.get("name", "")
            parts = service_name.split("/")
            if len(parts) >= 4:
                discovered_locations.add(f"projects/{parts[1]}/locations/{parts[3]}")

        services_request = (
            client.projects()
            .locations()
            .services()
            .list_next(
                previous_request=services_request,
                previous_response=services_response,
            )
        )

    if not discovered_locations:
        logger.warning(
            "Cloud Run location discovery fell back to service-based probing but found no locations for project %s. "
            "Skipping sync to preserve existing data.",
            project_id,
        )
        return None

    normalized_locations = sorted(discovered_locations)
    logger.info(
        "Discovered %s Cloud Run locations via fallback service probing for project %s.",
        len(normalized_locations),
        project_id,
    )
    return normalized_locations


@timeit
def discover_cloud_run_locations(
    client: Resource,
    project_id: str,
    credentials: GoogleCredentials | None = None,
) -> list[str] | None:
    """
    Discover Cloud Run locations for a project.

    Returns:
        list[str]: Sorted, deduped location resource names on successful discovery.
        None: Discovery failed in a way that should preserve last-known-good data.
    """
    try:
        resolved_credentials = credentials or get_gcp_credentials()
        v1_client = build_client("run", "v1", credentials=resolved_credentials)
        request = v1_client.projects().locations().list(name=f"projects/{project_id}")
    except RuntimeError as e:
        logger.warning(
            "Could not initialize the Cloud Run v1 discovery helper for project %s: %s. "
            "Falling back to service-based discovery.",
            project_id,
            e,
        )
        return _service_discovered_cloud_run_locations(client, project_id)

    discovered_locations: set[str] = set()
    while request is not None:
        try:
            response = request.execute()
        except HttpError as e:
            if is_api_disabled_error(e) or e.resp.status == 403:
                logger.warning(
                    "Could not retrieve Cloud Run locations on project %s due to permissions issues or API not enabled. "
                    "Skipping sync to preserve existing data.",
                    project_id,
                )
                return None

            logger.warning(
                "Cloud Run v1 location discovery failed for project %s with %s. Falling back to service-based discovery.",
                project_id,
                e,
            )
            return _service_discovered_cloud_run_locations(client, project_id)

        for location in response.get("locations", []):
            location_name = location.get("name")
            if location_name:
                discovered_locations.add(
                    _normalize_cloud_run_location_name(location_name),
                )

        request = (
            v1_client.projects()
            .locations()
            .list_next(
                previous_request=request,
                previous_response=response,
            )
        )

    if not discovered_locations:
        logger.warning(
            "Cloud Run v1 location discovery returned no locations for project %s. "
            "Falling back to service-based discovery.",
            project_id,
        )
        return _service_discovered_cloud_run_locations(client, project_id)

    normalized_locations = sorted(discovered_locations)
    logger.info(
        "Discovered %s cached Cloud Run locations for project %s.",
        len(normalized_locations),
        project_id,
    )
    return normalized_locations


def list_cloud_run_resources_for_location(
    *,
    fetcher: Callable[..., Iterable[object]],
    resource_type: str,
    location: str,
    project_id: str,
) -> list[dict]:
    location_name = _cloud_run_location_short_name(location)
    retry = build_cloud_run_resource_retry(
        resource_type=resource_type,
        location=location,
        project_id=project_id,
    )
    try:
        resources = [
            proto_message_to_dict(resource)
            for resource in fetcher(retry=retry, timeout=CLOUD_RUN_LIST_TIMEOUT)
        ]
    except NotFound:
        logger.debug(
            "Cloud Run %s not found in %s for project %s.",
            resource_type,
            location_name,
            project_id,
        )
        return []
    except PermissionDenied:
        logger.warning(
            "Access forbidden when trying to get Cloud Run %s in %s for project %s.",
            resource_type,
            location_name,
            project_id,
        )
        return []
    except GoogleAPICallError as e:
        logger.error(
            "Error getting Cloud Run %s in %s for project %s: %s",
            resource_type,
            location_name,
            project_id,
            e,
            exc_info=True,
        )
        raise

    logger.debug(
        "Found %s Cloud Run %s in %s for project %s",
        len(resources),
        resource_type,
        location_name,
        project_id,
    )
    return resources


@timeit
def fetch_cloud_run_resources_for_locations(
    *,
    locations: list[str],
    project_id: str,
    resource_type: str,
    fetch_for_location: Callable[[str], list[dict]],
    max_workers: int = DEFAULT_CLOUD_RUN_LOCATION_WORKERS,
) -> list[dict]:
    deduped_locations = list(dict.fromkeys(locations))
    if not deduped_locations:
        logger.info(
            "No Cloud Run locations to query for %s in project %s.",
            resource_type,
            project_id,
        )
        return []

    worker_count = min(max_workers, len(deduped_locations))
    logger.info(
        "Fetching Cloud Run %s across %s cached locations for project %s with max_workers=%s.",
        resource_type,
        len(deduped_locations),
        project_id,
        worker_count,
    )

    if worker_count <= 1:
        all_resources = []
        nonempty_locations = 0
        for location in deduped_locations:
            location_resources = fetch_for_location(location)
            if location_resources:
                nonempty_locations += 1
                all_resources.extend(location_resources)
        logger.info(
            "Collected %s Cloud Run %s across %s/%s queried locations for project %s.",
            len(all_resources),
            resource_type,
            nonempty_locations,
            len(deduped_locations),
            project_id,
        )
        return all_resources

    resources_by_location: dict[str, list[dict]] = {}
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(fetch_for_location, location): location
            for location in deduped_locations
        }
        for future in as_completed(futures):
            location = futures[future]
            resources_by_location[location] = future.result()

    all_resources = []
    nonempty_locations = 0
    for location in deduped_locations:
        location_resources = resources_by_location[location]
        if location_resources:
            nonempty_locations += 1
            all_resources.extend(location_resources)

    logger.info(
        "Collected %s Cloud Run %s across %s/%s queried locations for project %s.",
        len(all_resources),
        resource_type,
        nonempty_locations,
        len(deduped_locations),
        project_id,
    )
    return all_resources
