import logging
from collections.abc import Callable
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

from google.api_core.exceptions import GoogleAPICallError
from google.api_core.exceptions import PermissionDenied
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError
from google.cloud.artifactregistry_v1 import ArtifactRegistryClient

from cartography.util import timeit

logger = logging.getLogger(__name__)

ARTIFACT_REGISTRY_LOAD_BATCH_SIZE = 1000
DEFAULT_ARTIFACT_REGISTRY_WORKERS = 8

ItemT = TypeVar("ItemT")
ResultT = TypeVar("ResultT")


def fetch_artifact_registry_resources(
    *,
    items: list[ItemT],
    fetch_for_item: Callable[[ItemT], ResultT],
    resource_type: str,
    project_id: str,
    max_workers: int = DEFAULT_ARTIFACT_REGISTRY_WORKERS,
) -> list[ResultT]:
    if not items:
        return []

    worker_count = max(1, min(max_workers, len(items)))
    logger.info(
        "Fetching Artifact Registry %s for project %s across %d item(s) with max_workers=%d.",
        resource_type,
        project_id,
        len(items),
        worker_count,
    )

    if worker_count <= 1:
        return [fetch_for_item(item) for item in items]

    results_by_index: dict[int, ResultT] = {}
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(fetch_for_item, item): index
            for index, item in enumerate(items)
        }
        for future in as_completed(futures):
            results_by_index[futures[future]] = future.result()

    return [results_by_index[index] for index in range(len(items))]


@timeit
def get_artifact_registry_locations(
    client: ArtifactRegistryClient,
    project_id: str,
) -> list[str] | None:
    """
    Gets all available Artifact Registry locations for a project.
    """
    try:
        locations = [
            location.location_id
            for location in client.list_locations(
                request={"name": f"projects/{project_id}"}
            ).locations
            if location.location_id
        ]

        logger.info(
            "Found %d Artifact Registry locations for project %s.",
            len(locations),
            project_id,
        )
        return locations

    except PermissionDenied as e:
        logger.warning(
            "Missing permissions for Artifact Registry locations in project %s. "
            "Skipping Artifact Registry cleanup for this project. (%s)",
            project_id,
            type(e).__name__,
        )
        return None
    except (DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            "Failed to get Artifact Registry locations for project %s due to auth error. "
            "Skipping Artifact Registry cleanup for this project. (%s)",
            project_id,
            type(e).__name__,
        )
        return None
    except GoogleAPICallError:
        logger.error(
            "Unexpected error getting Artifact Registry locations for project %s.",
            project_id,
            exc_info=True,
        )
        raise
