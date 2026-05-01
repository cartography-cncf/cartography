import asyncio
import json
import logging

import httpx
import neo4j
from google.auth.credentials import Credentials as GoogleCredentials
from google.auth.transport.requests import Request

from cartography.graph.job import GraphJob
from cartography.intel.gcp.artifact_registry.util import (
    ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
)
from cartography.intel.gcp.artifact_registry.util import load_matchlinks_with_progress
from cartography.intel.gcp.artifact_registry.util import (
    load_nodes_without_relationships,
)
from cartography.models.gcp.artifact_registry.platform_image import (
    GCPArtifactRegistryContainerImageContainsPlatformImageRel,
)
from cartography.models.gcp.artifact_registry.platform_image import (
    GCPArtifactRegistryContainerImageToPlatformImageRel,
)
from cartography.models.gcp.artifact_registry.platform_image import (
    GCPArtifactRegistryPlatformImageSchema,
)
from cartography.models.gcp.artifact_registry.platform_image import (
    GCPArtifactRegistryProjectToPlatformImageRel,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Media types that indicate a multi-architecture manifest list
MANIFEST_LIST_MEDIA_TYPES = {
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.index.v1+json",
}


def parse_docker_image_uri(uri: str) -> tuple[str, str, str] | None:
    """
    Parse a Docker image URI into registry, image path, and reference components.

    :param uri: Docker image URI (e.g., us-docker.pkg.dev/project/repo/image@sha256:...)
    :return: Tuple of (registry, image_path, reference) or None if parsing fails.
    """
    if not uri:
        return None

    if "@" in uri:
        base, reference = uri.rsplit("@", 1)
    elif ":" in uri and "-docker.pkg.dev" in uri:
        parts = uri.split("/")
        if ":" in parts[-1]:
            base = uri.rsplit(":", 1)[0]
            reference = uri.rsplit(":", 1)[1]
        else:
            return None
    else:
        return None

    parts = base.split("/")
    if len(parts) < 4:
        return None

    registry = parts[0]
    image_path = "/".join(parts[1:])
    return registry, image_path, reference


def build_manifest_url(registry: str, image_path: str, reference: str) -> str:
    return f"https://{registry}/v2/{image_path}/manifests/{reference}"


def build_blob_url(registry: str, image_path: str, digest: str) -> str:
    return f"https://{registry}/v2/{image_path}/blobs/{digest}"


async def get_manifest_list_async(
    http_client: httpx.AsyncClient,
    auth_token: str,
    image_uri: str,
) -> list[dict]:
    """
    Gets the manifest list from the Docker Registry API for a multi-arch image asynchronously.

    :param http_client: httpx AsyncClient for making requests.
    :param auth_token: GCP OAuth token for authentication.
    :param image_uri: The Docker image URI.
    :return: List of platform manifest dicts from the manifest list.
    """
    parsed = parse_docker_image_uri(image_uri)
    if not parsed:
        logger.debug(f"Could not parse image URI: {image_uri}")
        return []

    registry, image_path, reference = parsed
    manifest_url = build_manifest_url(registry, image_path, reference)

    try:
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Accept": ", ".join(MANIFEST_LIST_MEDIA_TYPES),
        }

        response = await http_client.get(manifest_url, headers=headers, timeout=30.0)
        response.raise_for_status()

        manifest_data = response.json()

        # Return the manifests array from the manifest list
        return manifest_data.get("manifests", [])

    except httpx.HTTPError as e:
        logger.warning(f"Failed to fetch manifest from {manifest_url}: {e}")
        return []
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse manifest JSON from {manifest_url}: {e}")
        return []


async def get_all_manifests_async(
    credentials: GoogleCredentials,
    docker_artifacts_raw: list[dict],
    max_concurrent: int = 50,
) -> list[dict]:
    """
    Gets manifests for all multi-arch images in parallel with non-blocking I/O.

    :param credentials: GCP credentials for authentication.
    :param docker_artifacts_raw: List of raw Docker artifact data.
    :param max_concurrent: Maximum number of concurrent HTTP requests.
    :return: List of all transformed manifest dicts.
    """
    # Refresh credentials upfront (synchronous operation)
    if not credentials.valid:
        credentials.refresh(Request())

    auth_token = credentials.token
    all_manifests: list[dict] = []
    semaphore = asyncio.Semaphore(max_concurrent)

    # Filter to only multi-arch images
    multi_arch_artifacts = [
        artifact
        for artifact in docker_artifacts_raw
        if artifact.get("mediaType", "") in MANIFEST_LIST_MEDIA_TYPES
    ]

    if not multi_arch_artifacts:
        return []

    async def get_single_manifest(
        artifact: dict, http_client: httpx.AsyncClient
    ) -> list[dict]:
        """Gets and transforms manifest for a single artifact."""
        async with semaphore:
            artifact_name = artifact.get("name", "")
            artifact_uri = artifact.get("uri", "")
            project_id = artifact_name.split("/")[1] if "/" in artifact_name else ""

            manifest_entries = await get_manifest_list_async(
                http_client, auth_token, artifact_uri
            )
            if manifest_entries:
                return transform_manifests(manifest_entries, artifact_name, project_id)
            return []

    async with httpx.AsyncClient() as http_client:
        # Create tasks for all multi-arch images
        tasks = [
            asyncio.create_task(get_single_manifest(artifact, http_client))
            for artifact in multi_arch_artifacts
        ]

        total = len(tasks)
        logger.info(
            f"Getting manifests for {total} multi-arch images with {max_concurrent} concurrent connections..."
        )

        if not tasks:
            return []

        # Progress tracking
        progress_interval = max(1, min(100, total // 10 or 1))
        completed = 0

        for task in asyncio.as_completed(tasks):
            manifests = await task
            completed += 1

            if completed % progress_interval == 0 or completed == total:
                percent = (completed / total) * 100
                logger.info(
                    "Got manifests for %d/%d images (%.1f%%)",
                    completed,
                    total,
                    percent,
                )

            if manifests:
                all_manifests.extend(manifests)

    logger.info(f"Successfully got manifests for {len(all_manifests)} platform images")
    return all_manifests


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
    if not data:
        return

    schema = GCPArtifactRegistryPlatformImageSchema()
    load_nodes_without_relationships(
        neo4j_session,
        schema,
        data,
        batch_size=ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
        progress_description=(
            f"Artifact Registry platform image nodes for project {project_id}"
        ),
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )
    # Platform images only have the static Image label from the node phase.
    # Relationship phases are modeled as MatchLinks between existing nodes.
    load_matchlinks_with_progress(
        neo4j_session,
        GCPArtifactRegistryProjectToPlatformImageRel(),
        data,
        batch_size=ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
        progress_description=(
            "Artifact Registry platform image project RESOURCE relationships "
            f"for project {project_id}"
        ),
        lastupdated=update_tag,
        PROJECT_ID=project_id,
        _sub_resource_label="GCPProject",
        _sub_resource_id=project_id,
    )

    load_matchlinks_with_progress(
        neo4j_session,
        GCPArtifactRegistryContainerImageToPlatformImageRel(),
        data,
        batch_size=ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
        progress_description=(
            f"Artifact Registry platform image HAS_MANIFEST relationships for project {project_id}"
        ),
        lastupdated=update_tag,
        PROJECT_ID=project_id,
        _sub_resource_label="GCPProject",
        _sub_resource_id=project_id,
    )
    load_matchlinks_with_progress(
        neo4j_session,
        GCPArtifactRegistryContainerImageContainsPlatformImageRel(),
        data,
        batch_size=ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
        progress_description=(
            f"Artifact Registry platform image CONTAINS_IMAGE relationships for project {project_id}"
        ),
        lastupdated=update_tag,
        PROJECT_ID=project_id,
        _sub_resource_label="GCPProject",
        _sub_resource_id=project_id,
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
    # The split write path attaches these relationships with MatchLinks, so
    # clean them explicitly after node cleanup has used the project RESOURCE
    # edge to scope stale node deletion.
    GraphJob.from_matchlink(
        GCPArtifactRegistryProjectToPlatformImageRel(),
        "GCPProject",
        common_job_parameters["PROJECT_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)
    GraphJob.from_matchlink(
        GCPArtifactRegistryContainerImageToPlatformImageRel(),
        "GCPProject",
        common_job_parameters["PROJECT_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)
    GraphJob.from_matchlink(
        GCPArtifactRegistryContainerImageContainsPlatformImageRel(),
        "GCPProject",
        common_job_parameters["PROJECT_ID"],
        common_job_parameters["UPDATE_TAG"],
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
    Syncs GCP Artifact Registry image manifests for Docker artifacts using async/concurrent fetching.

    :param neo4j_session: The Neo4j session.
    :param credentials: GCP credentials for Docker Registry API calls.
    :param docker_artifacts_raw: List of raw Docker artifact data from the API.
    :param project_id: The GCP project ID.
    :param update_tag: The update tag for this sync.
    :param common_job_parameters: Common job parameters for cleanup.
    """
    logger.info(f"Syncing Artifact Registry image manifests for project {project_id}.")

    # Get all manifests concurrently using async
    # Use get_event_loop() + run_until_complete() to avoid tearing down loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # No event loop in current thread, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    all_manifests = loop.run_until_complete(
        get_all_manifests_async(credentials, docker_artifacts_raw)
    )

    if not all_manifests:
        logger.info(
            f"No Artifact Registry image manifests found for project {project_id}."
        )
    else:
        load_manifests(neo4j_session, all_manifests, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_manifests(neo4j_session, cleanup_job_params)
