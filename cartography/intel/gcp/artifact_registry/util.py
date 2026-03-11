import logging
from typing import Any

from google.api_core.exceptions import GoogleAPICallError
from google.api_core.exceptions import PermissionDenied
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError
from google.cloud.artifactregistry_v1 import ArtifactRegistryClient
from google.protobuf.json_format import MessageToDict

from cartography.util import timeit

logger = logging.getLogger(__name__)


def artifact_registry_message_to_dict(message: Any) -> dict[str, Any]:
    """
    Convert a protobuf or proto-plus message to the lowerCamelCase dict shape
    used by the existing Artifact Registry transforms.
    """
    if isinstance(message, dict):
        return message

    protobuf_message = getattr(message, "_pb", message)
    return MessageToDict(
        protobuf_message,
        preserving_proto_field_name=False,
    )


def classify_artifact_registry_error(exc: Exception) -> str | None:
    """
    Return a coarse error class for Artifact Registry calls that should be skipped.
    """
    if isinstance(exc, (DefaultCredentialsError, RefreshError, PermissionDenied)):
        return "permission_denied"

    if not isinstance(exc, GoogleAPICallError):
        return None

    lowered = str(exc).lower()
    if "billing_disabled" in lowered or "requires billing to be enabled" in lowered:
        return "billing_disabled"
    if (
        "accessnotconfigured" in lowered
        or "service_disabled" in lowered
        or "api has not been used" in lowered
        or "is not enabled" in lowered
        or "it is disabled" in lowered
    ):
        return "api_disabled"
    if (
        "permission denied" in lowered
        or "insufficientpermissions" in lowered
        or "iam_permission_denied" in lowered
        or "forbidden" in lowered
    ):
        return "permission_denied"
    return None


@timeit
def get_artifact_registry_locations(
    client: ArtifactRegistryClient, project_id: str
) -> list[str]:
    """
    Gets all available Artifact Registry locations for a project.
    """
    try:
        res = client.list_locations(request={"name": f"projects/{project_id}"})
        locations = [
            location.location_id for location in res.locations if location.location_id
        ]

        logger.info(
            f"Found {len(locations)} Artifact Registry locations for project {project_id}"
        )
        return locations

    except (GoogleAPICallError, DefaultCredentialsError, RefreshError) as e:
        classification = classify_artifact_registry_error(e)
        if classification == "billing_disabled":
            logger.warning(
                "Artifact Registry billing is disabled for project %s. Skipping Artifact Registry sync for this project.",
                project_id,
            )
            return []
        if classification == "api_disabled":
            logger.info(
                "Artifact Registry API appears disabled for project %s. Skipping Artifact Registry sync for this project.",
                project_id,
            )
            return []
        if classification == "permission_denied":
            logger.warning(
                "Missing permissions for Artifact Registry in project %s. Skipping Artifact Registry sync for this project.",
                project_id,
            )
            return []
        logger.error(
            f"Failed to get Artifact Registry locations for project {project_id}: {e}",
        )
        raise
