"""
Utility functions for GCP Vertex AI intel modules.
"""

import logging
from collections.abc import Callable
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from typing import cast

import backoff
from google.api_core.exceptions import GoogleAPICallError
from google.api_core.exceptions import NotFound
from google.api_core.exceptions import PermissionDenied
from google.api_core.exceptions import ServerError
from google.api_core.exceptions import TooManyRequests
from google.auth.credentials import Credentials as GoogleCredentials

from cartography.intel.gcp.util import GCP_API_BACKOFF_BASE
from cartography.intel.gcp.util import gcp_api_backoff_handler
from cartography.intel.gcp.util import GCP_API_BACKOFF_MAX
from cartography.intel.gcp.util import gcp_api_giveup_handler
from cartography.intel.gcp.util import GCP_API_MAX_RETRIES
from cartography.intel.gcp.util import proto_message_to_dict
from cartography.util import timeit

logger = logging.getLogger(__name__)

DEFAULT_VERTEX_AI_LOCATION_WORKERS = 8


def get_vertex_credentials(aiplatform_or_credentials: Any) -> GoogleCredentials:
    credentials = getattr(
        getattr(aiplatform_or_credentials, "_http", None), "credentials", None
    )
    if credentials is not None:
        return cast(GoogleCredentials, credentials)
    return cast(GoogleCredentials, aiplatform_or_credentials)


@backoff.on_exception(  # type: ignore[misc]
    backoff.expo,
    (ServerError, TooManyRequests),
    max_tries=GCP_API_MAX_RETRIES,
    on_backoff=gcp_api_backoff_handler,
    on_giveup=gcp_api_giveup_handler,
    logger=None,
    base=GCP_API_BACKOFF_BASE,
    max_value=GCP_API_BACKOFF_MAX,
)
def _list_vertex_ai_resources_with_retry(fetcher: Callable[[], Any]) -> list[dict]:
    return [proto_message_to_dict(resource) for resource in fetcher()]


def list_vertex_ai_resources_for_location(
    *,
    fetcher: Callable[[], Any],
    resource_type: str,
    location: str,
    project_id: str,
) -> list[dict]:
    try:
        resources = _list_vertex_ai_resources_with_retry(fetcher)
    except NotFound:
        logger.debug(
            "Vertex AI %s not found in %s for project %s. This location may not have any %s.",
            resource_type,
            location,
            project_id,
            resource_type,
        )
        return []
    except PermissionDenied:
        logger.warning(
            "Access forbidden when trying to get Vertex AI %s in %s for project %s.",
            resource_type,
            location,
            project_id,
        )
        return []
    except GoogleAPICallError as e:
        logger.error(
            "Error getting Vertex AI %s in %s for project %s: %s",
            resource_type,
            location,
            project_id,
            e,
            exc_info=True,
        )
        raise

    logger.debug(
        "Found %s Vertex AI %s in %s for project %s",
        len(resources),
        resource_type,
        location,
        project_id,
    )
    return resources


@timeit
def fetch_vertex_ai_resources_for_locations(
    *,
    locations: list[str],
    project_id: str,
    resource_type: str,
    fetch_for_location: Callable[[str], list[dict]],
    max_workers: int = DEFAULT_VERTEX_AI_LOCATION_WORKERS,
) -> list[dict]:
    deduped_locations = list(dict.fromkeys(locations))
    if not deduped_locations:
        logger.info(
            "No Vertex AI locations to query for %s in project %s.",
            resource_type,
            project_id,
        )
        return []

    worker_count = min(max_workers, len(deduped_locations))
    logger.info(
        "Fetching Vertex AI %s across %s cached locations for project %s with max_workers=%s.",
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
            "Collected %s Vertex AI %s across %s/%s queried locations for project %s.",
            len(all_resources),
            resource_type,
            nonempty_locations,
            len(deduped_locations),
            project_id,
        )
        return all_resources

    resources_by_location = {}
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
        "Collected %s Vertex AI %s across %s/%s queried locations for project %s.",
        len(all_resources),
        resource_type,
        nonempty_locations,
        len(deduped_locations),
        project_id,
    )
    return all_resources


def handle_vertex_api_response(
    response: Any,
    resource_type: str,
    location: str,
    project_id: str,
) -> tuple[dict | None, bool]:
    """
    Handle HTTP response from Vertex AI API with common error patterns.

    :param response: requests.Response object from API call
    :param resource_type: Type of resource being fetched (e.g., "models", "endpoints")
    :param location: GCP location/region
    :param project_id: GCP project ID
    :return: Tuple of (response_data, should_continue)
             - If successful: (json_data, True)
             - If error: (None, False)
    """
    if response.status_code == 404:
        logger.debug(
            "Vertex AI %s not found in %s for project %s. This location may not have any %s.",
            resource_type,
            location,
            project_id,
            resource_type,
        )
        return None, False
    elif response.status_code == 403:
        logger.warning(
            "Access forbidden when trying to get Vertex AI %s in %s for project %s.",
            resource_type,
            location,
            project_id,
        )
        return None, False
    elif response.status_code != 200:
        logger.error(
            "Error getting Vertex AI %s in %s for project %s: HTTP %s - %s",
            resource_type,
            location,
            project_id,
            response.status_code,
            response.reason,
            exc_info=False,
        )
        return None, False

    # Success - return parsed JSON
    return response.json(), True


def paginate_vertex_api(
    url: str,
    headers: dict[str, str] | None,
    resource_type: str,
    response_key: str,
    location: str,
    project_id: str,
    session: Any | None = None,
) -> list[dict]:
    """
    Handle paginated requests to Vertex AI regional endpoints.

    :param url: Base API URL (without pagination params)
    :param headers: Optional HTTP headers
    :param resource_type: Type of resource (for logging)
    :param response_key: Key in JSON response containing the resource list
    :param location: GCP location/region
    :param project_id: GCP project ID
    :param session: Optional authorized session used to execute requests
    :return: List of all resources across all pages
    """
    import requests

    resources = []
    page_token = None
    request_headers = headers or {}

    while True:
        params: dict[str, str] = {}
        if page_token:
            params["pageToken"] = page_token

        if session is not None:
            response = session.get(url, headers=request_headers, params=params)
        else:
            response = requests.get(url, headers=request_headers, params=params)

        # Handle response with common error patterns
        data, should_continue = handle_vertex_api_response(
            response, resource_type, location, project_id
        )

        if not should_continue or data is None:
            return []

        # Extract resources from this page
        resources.extend(data.get(response_key, []))

        # Check for next page
        page_token = data.get("nextPageToken")
        if not page_token:
            break

    logger.debug(
        "Found %s Vertex AI %s in %s for project %s",
        len(resources),
        resource_type,
        location,
        project_id,
    )
    return resources
