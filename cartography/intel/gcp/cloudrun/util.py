"""
Utility functions for GCP Cloud Run intel module.
"""

import logging

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


def discover_cloud_run_locations(client: Resource, project_id: str) -> set[str]:
    """
    Discovers GCP locations with Cloud Run resources.

    Uses the v1 API's locations.list() method to get all available Cloud Run regions.
    This ensures we don't miss regions that only have jobs (no services).
    Falls back to discovering via services list if the v1 API call fails.
    """
    try:
        # Use v1 API's locations.list() to get all Cloud Run regions
        from cartography.intel.gcp.clients import build_client
        from cartography.intel.gcp.clients import get_gcp_credentials

        credentials = get_gcp_credentials()
        v1_client = build_client("run", "v1", credentials=credentials)

        parent = f"projects/{project_id}"
        request = v1_client.projects().locations().list(name=parent)

        locations_set = set()
        while request is not None:
            response = request.execute()
            for location in response.get("locations", []):
                location_name = location.get(
                    "name"
                )  # e.g., projects/foo/locations/us-central1
                if location_name:
                    locations_set.add(location_name)
            request = (
                v1_client.projects()
                .locations()
                .list_next(
                    previous_request=request,
                    previous_response=response,
                )
            )

        if locations_set:
            logger.debug(
                f"Discovered {len(locations_set)} Cloud Run locations via v1 API"
            )
            return locations_set
        else:
            logger.warning(
                "v1 API returned no locations, falling back to service-based discovery"
            )

    except HttpError as e:
        # Only fall back for HTTP/API errors (e.g., API not enabled, 404, etc.)
        # Auth errors (DefaultCredentialsError, RefreshError) will propagate
        # since the fallback would also fail with the same auth issue
        logger.warning(
            f"Could not discover locations via v1 API: {e}. "
            f"Falling back to discovery via services list.",
        )

    # Fallback: discover locations by extracting them from service resource names
    logger.debug("Using service-based discovery for Cloud Run locations")
    services_parent = f"projects/{project_id}/locations/-"
    services_request = (
        client.projects().locations().services().list(parent=services_parent)
    )

    locations_set = set()
    while services_request is not None:
        services_response = services_request.execute()
        services = services_response.get("services", [])

        # Extract unique locations from service resource names
        # Format: projects/{project}/locations/{location}/services/{service}
        for service in services:
            service_name = service.get("name", "")
            parts = service_name.split("/")
            if len(parts) >= 4:
                # Reconstruct the location resource name: projects/{project}/locations/{location}
                locations_set.add(f"projects/{parts[1]}/locations/{parts[3]}")

        services_request = (
            client.projects()
            .locations()
            .services()
            .list_next(
                previous_request=services_request,
                previous_response=services_response,
            )
        )

    return locations_set
