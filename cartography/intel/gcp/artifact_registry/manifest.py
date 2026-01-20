import json
import logging

import neo4j
import requests
from google.auth.credentials import Credentials as GoogleCredentials
from google.auth.transport.requests import Request

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.artifact_registry.platform_image import (
    GCPArtifactRegistryPlatformImageSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Media types that indicate a multi-architecture manifest list
MANIFEST_LIST_MEDIA_TYPES = {
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.index.v1+json",
}


def _get_registry_url_from_uri(uri: str) -> tuple[str, str] | None:
    """
    Parses a Docker image URI to extract the registry URL and reference.

    :param uri: Docker image URI (e.g., us-docker.pkg.dev/project/repo/image@sha256:...)
    :return: Tuple of (registry_base_url, manifest_path) or None if parsing fails.
    """
    # URI format: {location}-docker.pkg.dev/{project}/{repo}/{image}@{digest}
    # or: {location}-docker.pkg.dev/{project}/{repo}/{image}:{tag}
    if not uri:
        return None

    # Split off the digest or tag
    if "@" in uri:
        base, reference = uri.rsplit("@", 1)
    elif ":" in uri and "-docker.pkg.dev" in uri:
        # Find the last colon that's part of the tag (not the port)
        parts = uri.split("/")
        if ":" in parts[-1]:
            base = uri.rsplit(":", 1)[0]
            reference = uri.rsplit(":", 1)[1]
        else:
            return None
    else:
        return None

    # Parse the base to get registry and image path
    # base = {location}-docker.pkg.dev/{project}/{repo}/{image}
    parts = base.split("/")
    if len(parts) < 4:
        return None

    registry = parts[0]
    image_path = "/".join(parts[1:])

    manifest_url = f"https://{registry}/v2/{image_path}/manifests/{reference}"
    return manifest_url, reference


@timeit
def get_manifest_list(
    credentials: GoogleCredentials,
    image_uri: str,
) -> list[dict]:
    """
    Fetches the manifest list from the Docker Registry API for a multi-arch image.

    :param credentials: GCP credentials for authentication.
    :param image_uri: The Docker image URI.
    :return: List of platform manifest dicts from the manifest list.
    """
    parsed = _get_registry_url_from_uri(image_uri)
    if not parsed:
        logger.debug(f"Could not parse image URI: {image_uri}")
        return []

    manifest_url, _ = parsed

    try:
        # Refresh credentials if needed
        if not credentials.valid:
            credentials.refresh(Request())

        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Accept": ", ".join(MANIFEST_LIST_MEDIA_TYPES),
        }

        response = requests.get(manifest_url, headers=headers, timeout=30)
        response.raise_for_status()

        manifest_data = response.json()

        # Return the manifests array from the manifest list
        return manifest_data.get("manifests", [])

    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch manifest from {manifest_url}: {e}")
        return []
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse manifest JSON from {manifest_url}: {e}")
        return []


def transform_manifests(
    manifest_entries: list[dict],
    parent_artifact_id: str,
    project_id: str,
) -> list[dict]:
    """
    Transforms manifest list entries into manifest node dicts.

    :param manifest_entries: List of manifest entries from the manifest list.
    :param parent_artifact_id: The ID of the parent multi-arch artifact.
    :param project_id: The GCP project ID.
    :return: List of transformed manifest dicts.
    """
    transformed: list[dict] = []

    for entry in manifest_entries:
        digest = entry.get("digest", "")
        platform = entry.get("platform", {})

        transformed.append(
            {
                "id": (
                    f"{parent_artifact_id}@{digest}" if digest else parent_artifact_id
                ),
                "digest": digest,
                "architecture": platform.get("architecture"),
                "os": platform.get("os"),
                "os_version": platform.get("os.version"),
                "os_features": platform.get("os.features"),
                "variant": platform.get("variant"),
                "media_type": entry.get("mediaType"),
                "parent_artifact_id": parent_artifact_id,
                "project_id": project_id,
            }
        )

    return transformed


@timeit
def load_manifests(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    """
    Loads GCPArtifactRegistryPlatformImage nodes and their relationships.
    """
    load(
        neo4j_session,
        GCPArtifactRegistryPlatformImageSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_manifests(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    """
    Cleans up stale Artifact Registry image manifests.
    """
    GraphJob.from_node_schema(
        GCPArtifactRegistryPlatformImageSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync_artifact_registry_manifests(
    neo4j_session: neo4j.Session,
    credentials: GoogleCredentials,
    docker_artifacts_raw: list[dict],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Syncs GCP Artifact Registry image manifests for Docker artifacts.

    :param neo4j_session: The Neo4j session.
    :param credentials: GCP credentials for Docker Registry API calls.
    :param docker_artifacts_raw: List of raw Docker artifact data from the API.
    :param project_id: The GCP project ID.
    :param update_tag: The update tag for this sync.
    :param common_job_parameters: Common job parameters for cleanup.
    """
    logger.info(f"Syncing Artifact Registry image manifests for project {project_id}.")

    all_manifests: list[dict] = []

    for artifact in docker_artifacts_raw:
        media_type = artifact.get("mediaType", "")

        # Only fetch manifests for multi-arch images
        if media_type not in MANIFEST_LIST_MEDIA_TYPES:
            continue

        artifact_name = artifact.get("name", "")
        artifact_uri = artifact.get("uri", "")

        manifest_entries = get_manifest_list(credentials, artifact_uri)
        if manifest_entries:
            manifests = transform_manifests(manifest_entries, artifact_name, project_id)
            all_manifests.extend(manifests)

    if not all_manifests:
        logger.info(
            f"No Artifact Registry image manifests found for project {project_id}."
        )
    else:
        load_manifests(neo4j_session, all_manifests, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_manifests(neo4j_session, cleanup_job_params)
