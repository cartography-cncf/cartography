import logging

from google.api_core.exceptions import PermissionDenied
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import Resource

from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_cloud_run_locations(client: Resource, project_id: str) -> list[dict]:
    locations: list[dict] = []
    try:
        parent = f"projects/{project_id}"
        request = client.projects().locations().list(name=parent)

        while request is not None:
            response = request.execute()
            locations.extend(response.get("locations", []))
            request = (
                client.projects()
                .locations()
                .list_next(
                    previous_request=request,
                    previous_response=response,
                )
            )
        return locations
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            f"Failed to get Cloud Run locations for project {project_id} due to permissions or auth error: {e}",
        )
        raise
