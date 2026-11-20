import asyncio
import json
import logging
from dataclasses import asdict
from dataclasses import dataclass
from typing import Any

import httpx
import neo4j
from google.auth.credentials import Credentials as GoogleCredentials
from google.auth.transport.requests import Request

from cartography.client.core.tx import run_write_query
from cartography.graph.job import GraphJob
from cartography.helpers import batch
from cartography.intel.gcp.artifact_registry.util import (
    ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
)
from cartography.intel.gcp.artifact_registry.util import load_matchlinks_with_progress
from cartography.intel.gcp.artifact_registry.util import (
    load_nodes_without_relationships,
)
from cartography.intel.gcp.artifact_registry.util import MANIFEST_LIST_MEDIA_TYPES
from cartography.models.gcp.artifact_registry.image import (
    GCPArtifactRegistryImageContainsImageMatchLink,
)
from cartography.models.gcp.artifact_registry.image import (
    GCPArtifactRegistryImageManifestChildNodeProperties,
)
from cartography.models.gcp.artifact_registry.image import (
    GCPArtifactRegistryImageManifestChildSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PlatformImageChanges:
    to_write: list[dict]
    unchanged_digests: list[str]
    gone_links: list[dict[str, str]]


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


def extract_digest_from_reference(reference: str | None) -> str | None:
    if not reference or "@" not in reference:
        return None
    digest = reference.rsplit("@", 1)[1]
    return digest or None


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
            parent_digest = extract_digest_from_reference(
                artifact_uri
            ) or extract_digest_from_reference(artifact_name)

            manifest_entries = await get_manifest_list_async(
                http_client, auth_token, artifact_uri
            )
            if manifest_entries:
                return transform_manifests(manifest_entries, parent_digest)
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
    parent_digest: str | None,
) -> list[dict]:
    """
    Transforms manifest list entries into manifest node dicts.

    :param manifest_entries: List of manifest entries from the manifest list.
    :param parent_digest: The digest of the parent multi-arch image.
    :return: List of transformed manifest dicts.
    """
    transformed: list[dict] = []

    for entry in manifest_entries:
        digest = entry.get("digest", "")
        # Registry manifest lists nest platform fields under "platform"; the
        # dockerImages API returns them at the top level of each imageManifests entry.
        platform = entry.get("platform") or entry

        transformed.append(
            {
                "digest": digest,
                "type": "image",
                "architecture": platform.get("architecture"),
                "os": platform.get("os"),
                "os_version": platform.get("os.version") or platform.get("osVersion"),
                "os_features": platform.get("os.features")
                or platform.get("osFeatures"),
                "variant": platform.get("variant"),
                "media_type": entry.get("mediaType"),
                "parent_digest": parent_digest,
                "child_digest": digest,
                "child_image_digests": [digest] if digest else [],
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
    Loads canonical GCPArtifactRegistryImage child nodes and CONTAINS_IMAGE relationships.
    """
    if not data:
        return

    schema = GCPArtifactRegistryImageManifestChildSchema()
    load_nodes_without_relationships(
        neo4j_session,
        schema,
        data,
        batch_size=ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
        progress_description=(
            f"Artifact Registry canonical platform image nodes for project {project_id}"
        ),
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )
    load_matchlinks_with_progress(
        neo4j_session,
        GCPArtifactRegistryImageContainsImageMatchLink(),
        data,
        batch_size=ARTIFACT_REGISTRY_LOAD_BATCH_SIZE,
        progress_description=(
            "Artifact Registry manifest-list CONTAINS_IMAGE relationships "
            f"for project {project_id}"
        ),
        lastupdated=update_tag,
        PROJECT_ID=project_id,
        _sub_resource_label="GCPProject",
        _sub_resource_id=project_id,
    )


# Every platform image property load_manifests writes besides the id, as
# (node property, transformed field). Read from the schema so that a property
# added there is compared too.
_PLATFORM_IMAGE_FIELDS = sorted(
    (node_property, ref.name)
    for node_property, ref in asdict(
        GCPArtifactRegistryImageManifestChildNodeProperties()
    ).items()
    if node_property != "id" and not ref.set_in_kwargs and not ref.set_by_analysis
)
_PLATFORM_IMAGE_LABELS = GCPArtifactRegistryImageManifestChildSchema().extra_node_labels

# Only this project's links. A manifest list has one CONTAINS_IMAGE link per
# platform image however many projects list it, scoped to the project that wrote
# it last. A link another project wrote last is written again, as before.
_SAVED_PLATFORM_IMAGES_QUERY = """
MATCH (parent:GCPArtifactRegistryImage)-[r:CONTAINS_IMAGE]->
      (child:GCPArtifactRegistryImage)
WHERE r._sub_resource_label = 'GCPProject' AND r._sub_resource_id = $project_id
RETURN
    parent.digest AS parent_digest,
    child.digest AS child_digest,
    [node_property IN $node_properties | child[node_property]] AS saved,
    labels(child) AS labels
"""

PLATFORM_IMAGE_REFRESH_BATCH_SIZE = 10_000


def _has_loaded_labels(labels: list[str], properties: dict[str, Any]) -> bool:
    """Whether a platform image has exactly the extra labels load_manifests gives it."""
    for label in {extra.label for extra in _PLATFORM_IMAGE_LABELS.labels}:
        wanted = any(
            all(properties.get(name) == value for name, value in extra.conditions)
            for extra in _PLATFORM_IMAGE_LABELS.labels
            if extra.label == label
        )
        if wanted != (label in labels):
            return False
    return True


@timeit
def get_platform_image_changes(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
) -> PlatformImageChanges:
    """
    Compares the project's listed platform images with the ones its graph holds.

    A platform image is unchanged when its manifest list links to it for this
    project and every property and label load_manifests writes already matches.
    """
    listed = {(row["parent_digest"], row["child_digest"]): row for row in data}
    node_properties = [node_property for node_property, _ in _PLATFORM_IMAGE_FIELDS]
    fields = [field for _, field in _PLATFORM_IMAGE_FIELDS]

    def _read_changes(
        tx: neo4j.Transaction,
    ) -> tuple[set[tuple[str, str]], list[dict[str, str]]]:
        unchanged: set[tuple[str, str]] = set()
        gone_links: list[dict[str, str]] = []
        result = tx.run(
            _SAVED_PLATFORM_IMAGES_QUERY,
            project_id=project_id,
            node_properties=node_properties,
        )
        for record in result:
            link = (record["parent_digest"], record["child_digest"])
            row = listed.get(link)
            if row is None:
                gone_links.append(
                    {"parent_digest": link[0], "child_digest": link[1]},
                )
            elif record["saved"] == [
                row.get(field) for field in fields
            ] and _has_loaded_labels(
                record["labels"], dict(zip(node_properties, record["saved"]))
            ):
                unchanged.add(link)
        return unchanged, gone_links

    unchanged, gone_links = neo4j_session.execute_read(_read_changes)
    to_write = [row for link, row in listed.items() if link not in unchanged]
    rewritten_digests = {row["child_digest"] for row in to_write}
    return PlatformImageChanges(
        to_write=to_write,
        unchanged_digests=sorted(
            {child for _, child in unchanged} - rewritten_digests,
        ),
        gone_links=gone_links,
    )


@timeit
def refresh_platform_images(
    neo4j_session: neo4j.Session,
    digests: list[str],
    update_tag: int,
) -> None:
    """
    Marks unchanged platform images as seen by this sync without writing them
    again. Their CONTAINS_IMAGE links keep the update tag of the sync that wrote
    them: cleanup is a set difference, so nothing reads it (see sync_manifests).
    """
    for digest_batch in batch(digests, size=PLATFORM_IMAGE_REFRESH_BATCH_SIZE):
        run_write_query(
            neo4j_session,
            """
            UNWIND $digests AS digest
            MATCH (child:GCPArtifactRegistryImage {digest: digest})
            SET child.lastupdated = $update_tag
            """,
            digests=digest_batch,
            update_tag=update_tag,
        )


@timeit
def delete_platform_image_links(
    neo4j_session: neo4j.Session,
    links: list[dict[str, str]],
    project_id: str,
) -> None:
    """
    Deletes the project's CONTAINS_IMAGE links that the listing no longer has.
    """
    for link_batch in batch(links, size=ARTIFACT_REGISTRY_LOAD_BATCH_SIZE):
        run_write_query(
            neo4j_session,
            """
            UNWIND $links AS link
            MATCH (:GCPArtifactRegistryImage {digest: link.parent_digest})
                  -[r:CONTAINS_IMAGE]->
                  (:GCPArtifactRegistryImage {digest: link.child_digest})
            WHERE r._sub_resource_label = 'GCPProject'
              AND r._sub_resource_id = $project_id
            DELETE r
            """,
            links=link_batch,
            project_id=project_id,
        )


@timeit
def sync_manifests(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
    cleanup_safe: bool,
) -> None:
    """
    Writes the project's platform images, rewriting only those that changed.

    A manifest list's platform images are fixed by its digest, so from one sync to
    the next almost none change. As with tags (see artifact.sync_docker_images),
    each listed manifest list and platform image pair is compared with the graph
    first. New and changed pairs go through load_manifests; unchanged platform
    images only get their lastupdated refreshed. Cleanup is a set difference: a
    link the listing no longer has is deleted. A platform image left with no
    link is then deleted by gcp_artifact_registry_orphan_cleanup.json.
    """
    changes = get_platform_image_changes(neo4j_session, data, project_id)
    logger.info(
        "Artifact Registry platform images for project %s: %d to write, "
        "%d unchanged, %d links gone.",
        project_id,
        len(changes.to_write),
        len(changes.unchanged_digests),
        len(changes.gone_links),
    )
    load_manifests(neo4j_session, changes.to_write, project_id, update_tag)
    refresh_platform_images(neo4j_session, changes.unchanged_digests, update_tag)
    if cleanup_safe:
        delete_platform_image_links(neo4j_session, changes.gone_links, project_id)


@timeit
def cleanup_manifests(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    """
    Cleans up stale Artifact Registry image manifest relationships.
    """
    GraphJob.from_matchlink(
        GCPArtifactRegistryImageContainsImageMatchLink(),
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
