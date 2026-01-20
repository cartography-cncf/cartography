import logging

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_artifact_registry_locations(client: Resource, project_id: str) -> list[str]:
    """
    Gets all available Artifact Registry locations for a project.
    """
    try:
        req = client.projects().locations().list(name=f"projects/{project_id}")
        res = req.execute()

        locations = [
            location.get("locationId")
            for location in res.get("locations", [])
            if location.get("locationId")
        ]

        logger.info(
            f"Found {len(locations)} Artifact Registry locations for project {project_id}"
        )
        return locations

    except HttpError as e:
        logger.error(
            f"Failed to get Artifact Registry locations for project {project_id}: {e}",
        )
        raise
