import logging

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import get_error_reason
from cartography.intel.gcp.util import is_api_disabled_error
from cartography.intel.gcp.util import is_billing_disabled_error
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_artifact_registry_locations(client: Resource, project_id: str) -> list[str]:
    """
    Gets all available Artifact Registry locations for a project.
    """
    try:
        req = client.projects().locations().list(name=f"projects/{project_id}")
        res = gcp_api_execute_with_retry(req)

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
        if is_billing_disabled_error(e):
            logger.warning(
                "Artifact Registry billing is disabled for project %s. Skipping Artifact Registry sync for this project. Full details: %s",
                project_id,
                e,
            )
            return []
        if is_api_disabled_error(e):
            logger.info(
                "Artifact Registry API appears disabled for project %s. Skipping Artifact Registry sync for this project. Full details: %s",
                project_id,
                e,
            )
            return []
        reason = get_error_reason(e)
        if reason in {"forbidden", "insufficientPermissions", "IAM_PERMISSION_DENIED"}:
            logger.warning(
                "Missing permissions for Artifact Registry in project %s. Skipping Artifact Registry sync for this project. Full details: %s",
                project_id,
                e,
            )
            return []
        logger.error(
            f"Failed to get Artifact Registry locations for project {project_id}: {e}",
        )
        raise
