"""
Utility functions for GCP Vertex AI intel modules.
"""

import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

logger = logging.getLogger(__name__)


def handle_vertex_api_response(
    response: Any,
    resource_type: str,
    location: str,
    project_id: str,
) -> Tuple[Optional[Dict], bool]:
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
            f"Vertex AI {resource_type} not found in {location} for project {project_id}. "
            f"This location may not have any {resource_type}."
        )
        return None, False
    elif response.status_code == 403:
        logger.warning(
            f"Access forbidden when trying to get Vertex AI {resource_type} in {location} "
            f"for project {project_id}."
        )
        return None, False
    elif response.status_code != 200:
        logger.error(
            f"Error getting Vertex AI {resource_type} in {location} for project {project_id}: "
            f"HTTP {response.status_code} - {response.reason}",
            exc_info=False,
        )
        return None, False

    # Success - return parsed JSON
    return response.json(), True


def paginate_vertex_api(
    url: str,
    headers: Dict[str, str],
    resource_type: str,
    response_key: str,
    location: str,
    project_id: str,
) -> List[Dict]:
    """
    Handle paginated requests to Vertex AI regional endpoints.

    :param url: Base API URL (without pagination params)
    :param headers: HTTP headers including Authorization
    :param resource_type: Type of resource (for logging)
    :param response_key: Key in JSON response containing the resource list
    :param location: GCP location/region
    :param project_id: GCP project ID
    :return: List of all resources across all pages
    """
    import requests

    resources = []
    page_token = None

    while True:
        params: Dict[str, str] = {}
        if page_token:
            params["pageToken"] = page_token

        response = requests.get(url, headers=headers, params=params)

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

    logger.info(
        f"Found {len(resources)} Vertex AI {resource_type} in {location} for project {project_id}"
    )
    return resources
