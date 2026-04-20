"""
Utility functions for GCP Cloud Run intel module.
"""

import logging
from collections.abc import Mapping
from typing import Optional
from typing import TypedDict

from google.auth.credentials import Credentials as GoogleCredentials

from cartography.intel.gcp.clients import build_authorized_session

logger = logging.getLogger(__name__)


class CloudRunContainerImageMetadata(TypedDict):
    container_image: str | None
    container_images: list[str]
    image_digest: str | None
    image_digests: list[str]


def _extract_image_digest(image: str | None) -> str | None:
    if not image or "@" not in image:
        return None
    _, digest = image.rsplit("@", 1)
    return digest or None


def extract_container_image_metadata(
    containers: list[dict] | None,
) -> CloudRunContainerImageMetadata:
    """
    Extract first-container compatibility fields plus complete container image metadata.
    """
    container_images: list[str] = []
    image_digests: list[str] = []

    for container in containers or []:
        image = container.get("image")
        if not image:
            continue
        if image not in container_images:
            container_images.append(image)

        digest = _extract_image_digest(image)
        if digest and digest not in image_digests:
            image_digests.append(digest)

    return {
        "container_image": container_images[0] if container_images else None,
        "container_images": container_images,
        "image_digest": image_digests[0] if image_digests else None,
        "image_digests": image_digests,
    }


def discover_cloud_run_locations(
    project_id: str,
    credentials: Optional[GoogleCredentials] = None,
) -> set[str] | None:
    """
    Discovers GCP locations with Cloud Run resources.

    Uses the Cloud Run v1 ``projects.locations.list`` endpoint directly via an
    authorized session. The GAPIC v2 clients do not expose a locations client,
    but this avoids the discovery client while still using the official API.
    """
    try:
        session = build_authorized_session(credentials=credentials)
    except RuntimeError as e:
        logger.warning(
            "Could not initialize credentials for Cloud Run location discovery on project %s - %s. "
            "Skipping Cloud Run sync to preserve existing data.",
            project_id,
            e,
        )
        return None

    locations_set = set()
    next_page_token: str | None = None
    url = f"https://run.googleapis.com/v1/projects/{project_id}/locations"

    while True:
        params = {}
        if next_page_token:
            params["pageToken"] = next_page_token
        response = session.get(url, params=params or None, timeout=120)
        if response.status_code in (403, 404):
            logger.warning(
                "Could not discover Cloud Run locations on project %s - HTTP %s. "
                "Skipping Cloud Run sync to preserve existing data.",
                project_id,
                response.status_code,
            )
            return None
        response.raise_for_status()

        payload = response.json()
        if not isinstance(payload, Mapping):
            raise TypeError(
                f"Unexpected Cloud Run locations payload type: {type(payload)!r}"
            )

        for location in payload.get("locations", []):
            if not isinstance(location, Mapping):
                continue
            location_name = location.get("name")
            if not isinstance(location_name, str) or not location_name:
                continue
            if not location_name.startswith("projects/"):
                location_name = f"projects/{location_name}"
            locations_set.add(location_name)

        next_page_token = payload.get("nextPageToken")
        if not isinstance(next_page_token, str) or not next_page_token:
            break

    logger.debug(
        "Discovered %d Cloud Run locations via v1 locations API on project %s.",
        len(locations_set),
        project_id,
    )

    return locations_set
