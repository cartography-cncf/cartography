"""
Utility functions for GCP Cloud Run intel module.
"""

import logging

from googleapiclient.discovery import Resource

logger = logging.getLogger(__name__)


def discover_cloud_run_locations(client: Resource, project_id: str) -> set[str]:
    """
    Discovers GCP locations with Cloud Run resources by listing services.

    The Cloud Run v2 API doesn't support listing locations directly via locations.list(),
    so we work around this by listing services with the location wildcard "-" and
    extracting unique locations from the service resource names.
    """
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
