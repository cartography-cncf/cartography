import logging
from typing import List

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_artifact_registry_locations(client: Resource, project_id: str) -> List[str]:
    """
    Gets all available Artifact Registry locations for a project.
    Filters to regions that commonly support Artifact Registry to improve sync performance.
    """
    try:
        req = client.projects().locations().list(name=f"projects/{project_id}")
        res = req.execute()

        # Filter to commonly-used regions to avoid excessive API calls
        # Reference: https://cloud.google.com/artifact-registry/docs/repositories/repo-locations
        supported_regions = {
            "us-central1",
            "us-east1",
            "us-east4",
            "us-west1",
            "us-west2",
            "us-west3",
            "us-west4",
            "europe-west1",
            "europe-west2",
            "europe-west3",
            "europe-west4",
            "europe-west6",
            "asia-east1",
            "asia-east2",
            "asia-northeast1",
            "asia-northeast2",
            "asia-northeast3",
            "asia-southeast1",
            "asia-southeast2",
            "australia-southeast1",
            "northamerica-northeast1",
            "southamerica-east1",
        }

        locations = []
        all_locations = res.get("locations", [])
        for location in all_locations:
            location_id = location.get("locationId")
            if location_id in supported_regions:
                locations.append(location_id)

        logger.info(
            f"Found {len(locations)} supported Artifact Registry locations "
            f"(filtered from {len(all_locations)} total) for project {project_id}"
        )
        return locations

    except HttpError as e:
        if e.resp.status == 403:
            logger.warning(
                f"Access forbidden when trying to get Artifact Registry locations for project {project_id}. "
                "Ensure the Artifact Registry API is enabled and you have the necessary permissions.",
            )
        elif e.resp.status == 404:
            logger.warning(
                f"Artifact Registry locations not found for project {project_id}. "
                "The Artifact Registry API may not be enabled.",
            )
        else:
            logger.error(
                f"Error getting Artifact Registry locations for project {project_id}: {e}",
                exc_info=True,
            )
        return []
