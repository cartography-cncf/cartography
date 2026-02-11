"""
GitLab Container Images Intelligence Module

Syncs container images from GitLab into the graph.
Images are fetched via the Docker Registry V2 API to get full manifest details.
"""

import logging
from typing import Any
from urllib.parse import urlparse

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gitlab.util import fetch_registry_blob
from cartography.intel.gitlab.util import fetch_registry_manifest
from cartography.intel.gitlab.util import get_paginated
from cartography.models.gitlab.container_image_layers import (
    GitLabContainerImageLayerSchema,
)
from cartography.models.gitlab.container_images import GitLabContainerImageSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Media types to accept when fetching manifests
# Includes both Docker and OCI formats, single images and manifest lists
MANIFEST_ACCEPT_HEADER = ", ".join(
    [
        "application/vnd.docker.distribution.manifest.v2+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.oci.image.index.v1+json",
    ]
)

# Media types that indicate a manifest list (multi-arch image)
MANIFEST_LIST_MEDIA_TYPES = {
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.index.v1+json",
}


def _parse_repository_location(location: str) -> tuple[str, str]:
    """
    Parse a repository location into registry URL and repository name.
    """
    parsed = urlparse(f"https://{location}" if "://" not in location else location)
    registry_url = f"https://{parsed.netloc}"
    # Repository name is the path without leading slash
    repository_name = parsed.path.lstrip("/")
    return registry_url, repository_name


def _get_manifest(
    gitlab_url: str,
    registry_url: str,
    repository_name: str,
    reference: str,
    token: str,
) -> dict[str, Any] | None:
    """
    Fetch a manifest from the Docker Registry V2 API.

    Handles 401 errors by refreshing the JWT token and retrying once.
    Returns None if the manifest is not found (404), allowing callers to skip deleted tags.
    """
    response = fetch_registry_manifest(
        gitlab_url,
        registry_url,
        repository_name,
        reference,
        token,
        accept_header=MANIFEST_ACCEPT_HEADER,
    )

    # Handle 404 errors gracefully - tag may have been deleted between list and fetch
    if response.status_code == 404:
        logger.debug(
            f"Manifest not found for {repository_name}:{reference} - tag may have been deleted"
        )
        return None

    response.raise_for_status()

    manifest = response.json()
    # Include the digest from response header (canonical digest)
    manifest["_digest"] = response.headers.get("Docker-Content-Digest")
    # Include the repository location for context
    manifest["_repository_name"] = repository_name
    manifest["_registry_url"] = registry_url
    manifest["_reference"] = reference

    return manifest


def get_container_images(
    gitlab_url: str,
    token: str,
    repositories: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Fetch container image manifests for all repositories via the Registry V2 API.

    For each repository, fetches tags and then retrieves the manifest for each tag.
    Returns raw manifest data for transformation, plus manifest lists for attestation discovery.

    Deduplication is scoped per repository to ensure complete attestation discovery.
    If the same digest appears in multiple repositories, each will be processed separately.
    """
    all_manifests: list[dict[str, Any]] = []
    manifest_lists: list[dict[str, Any]] = []
    seen_digests: dict[str, set[str]] = {}

    for repo in repositories:
        location = repo.get("location")
        project_id = repo.get("project_id")
        repository_id = repo.get("id")

        if not location or not project_id or not repository_id:
            logger.warning(f"Repository missing required fields: {repo}")
            continue

        # Parse location into registry URL and repository name
        # e.g., "registry.gitlab.com/group/project" -> ("https://registry.gitlab.com", "group/project")
        location = str(location)
        registry_url, repository_name = _parse_repository_location(location)

        # Initialize seen digests set for this repository
        if repository_name not in seen_digests:
            seen_digests[repository_name] = set()

        # Fetch tags for this repository
        tags = get_paginated(
            gitlab_url,
            token,
            f"/api/v4/projects/{project_id}/registry/repositories/{repository_id}/tags",
        )

        for tag in tags:
            tag_name = tag.get("name")
            if not tag_name:
                continue

            manifest = _get_manifest(
                gitlab_url, registry_url, repository_name, tag_name, token
            )  # can return an image or a manifest list

            # Skip if manifest not found (tag deleted between list and fetch)
            if manifest is None:
                continue

            # Deduplicate by digest within this repository (multiple tags can point to same image)
            digest = manifest.get("_digest")
            if not digest or digest in seen_digests[repository_name]:
                continue
            seen_digests[repository_name].add(digest)

            media_type = manifest.get("mediaType")
            is_manifest_list = media_type in MANIFEST_LIST_MEDIA_TYPES

            if is_manifest_list:
                # Save manifest list for buildx attestation discovery
                manifest_lists.append(manifest)
                # Also add to all_manifests so it becomes a ContainerImage node
                all_manifests.append(manifest)

                # For manifest lists, fetch child manifests (but skip attestation entries)
                child_manifests = manifest.get("manifests", [])
                expected_children = 0
                ingested_children = 0

                for child in child_manifests:
                    # Skip buildx attestation entries stored in child manifests - they'll be handled by attestations module
                    annotations = child.get("annotations", {})
                    if (
                        annotations.get("vnd.docker.reference.type")
                        == "attestation-manifest"
                    ):
                        continue

                    expected_children += 1
                    child_digest = child.get("digest")

                    if child_digest in seen_digests[repository_name]:
                        ingested_children += 1  # Already ingested
                        continue
                    seen_digests[repository_name].add(child_digest)

                    child_manifest = _get_manifest(
                        gitlab_url, registry_url, repository_name, child_digest, token
                    )

                    # Skip if child manifest not found (tag deleted between list and fetch)
                    if child_manifest is None:
                        logger.warning(
                            f"Failed to fetch child manifest {child_digest[:16]}... for manifest list "
                            f"{digest[:16]}... in {repository_name}. Child will be missing from graph."
                        )
                        continue

                    # Fetch config blob for child image
                    child_config = child_manifest.get("config")
                    if child_config and child_config.get("digest"):
                        try:
                            child_manifest["_config"] = fetch_registry_blob(
                                gitlab_url,
                                registry_url,
                                repository_name,
                                child_config["digest"],
                                token,
                            )
                        except Exception as e:
                            logger.warning(
                                f"Failed to fetch config blob for child {child_digest[:16]}...: {e}. "
                                f"Architecture metadata may be incomplete."
                            )

                    all_manifests.append(child_manifest)
                    ingested_children += 1

                # Log summary for this manifest list
                if expected_children > 0:
                    logger.info(
                        f"Manifest list {digest[:16]}... in {repository_name}: "
                        f"ingested {ingested_children}/{expected_children} platform images"
                    )
                    if ingested_children < expected_children:
                        logger.warning(
                            f"Manifest list {digest[:16]}... is missing "
                            f"{expected_children - ingested_children} child image(s). "
                            f"Trivy scans of missing platforms will not link to graph."
                        )
            else:
                # Fetch config blob for regular images to get architecture/os/variant properties
                config = manifest.get("config")
                if config and config.get("digest"):
                    manifest["_config"] = fetch_registry_blob(
                        gitlab_url,
                        registry_url,
                        repository_name,
                        config["digest"],
                        token,
                    )

                all_manifests.append(manifest)

    logger.info(
        f"Fetched {len(all_manifests)} unique image manifests and {len(manifest_lists)} manifest lists from {len(repositories)} repositories"
    )
    return all_manifests, manifest_lists


def transform_container_images(
    raw_manifests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Transform raw manifest data into the format expected by the schema.
    """
    transformed = []

    for manifest in raw_manifests:
        media_type = manifest.get("mediaType")
        is_manifest_list = media_type in MANIFEST_LIST_MEDIA_TYPES

        # Extract child image digests for manifest lists
        # Filter out attestation-manifest entries to match the ingestion logic
        child_image_digests = None
        if is_manifest_list:
            manifests_array = manifest.get("manifests", [])
            child_image_digests = [
                m.get("digest")
                for m in manifests_array
                if m.get("digest")
                and m.get("annotations", {}).get("vnd.docker.reference.type")
                != "attestation-manifest"
            ]

        # Extract architecture, os, variant and layer diff IDs from config blob (for regular images)
        config = manifest.get("_config", {})

        # Extract layer diff IDs from rootfs (used for Dockerfile matching and layer relationships)
        layer_diff_ids = None
        head_layer_diff_id = None
        tail_layer_diff_id = None
        if not is_manifest_list:
            rootfs = config.get("rootfs", {})
            diff_ids = rootfs.get("diff_ids")
            # Only set if there are actual layers, otherwise keep as None to skip relationship matching
            if diff_ids and isinstance(diff_ids, list) and len(diff_ids) > 0:
                layer_diff_ids = diff_ids
                head_layer_diff_id = diff_ids[0]  # First layer
                tail_layer_diff_id = diff_ids[-1]  # Last layer

        # Build URI from registry URL and repository name (e.g., registry.gitlab.com/group/project)
        registry_url = manifest.get("_registry_url", "")
        repository_name = manifest.get("_repository_name", "")
        # Strip https:// prefix from registry URL to get the host
        registry_host = urlparse(registry_url).netloc if registry_url else ""
        uri = (
            f"{registry_host}/{repository_name}"
            if registry_host and repository_name
            else None
        )

        transformed.append(
            {
                "digest": manifest.get("_digest"),
                "uri": uri,
                "media_type": media_type,
                "schema_version": manifest.get("schemaVersion"),
                "type": "manifest_list" if is_manifest_list else "image",
                "architecture": config.get("architecture"),
                "os": config.get("os"),
                "variant": config.get("variant"),
                "child_image_digests": child_image_digests,
                "layer_diff_ids": layer_diff_ids,
                "head_layer_diff_id": head_layer_diff_id,
                "tail_layer_diff_id": tail_layer_diff_id,
            }
        )

    logger.info(f"Transformed {len(transformed)} container images")
    return transformed


def transform_container_image_layers(
    raw_manifests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Transform raw manifest data into layer nodes with linked list structure.
    Extracts layers from regular images (not manifest lists) and creates:
    - NEXT relationships between consecutive layers (linked list)
    - HEAD relationships from first layer to images
    - TAIL relationships from last layer to images

    This follows the ECR pattern for queryable layer ordering.
    Layers are keyed by diff_id (uncompressed) for cross-provider deduplication.
    """
    layers_by_diff_id: dict[str, dict[str, Any]] = {}
    skipped_layers_count = 0

    for manifest in raw_manifests:
        media_type = manifest.get("mediaType")
        is_manifest_list = media_type in MANIFEST_LIST_MEDIA_TYPES

        # Skip manifest lists - they don't have layers
        if is_manifest_list:
            continue

        image_digest = manifest.get("_digest")
        layers = manifest.get("layers", [])
        config = manifest.get("_config", {})
        diff_ids_raw = config.get("rootfs", {}).get("diff_ids", [])

        # Ensure diff_ids is a list for type checking
        diff_ids: list[Any] = diff_ids_raw if isinstance(diff_ids_raw, list) else []

        # Process each layer in the chain
        for i, layer in enumerate(layers):
            layer_digest = layer.get("digest")
            if not layer_digest:
                logger.warning(
                    f"Skipping layer at index {i} in image {image_digest}: missing compressed digest"
                )
                skipped_layers_count += 1
                continue

            # Get diff_id from config (uncompressed layer ID)
            # diff_id is required for cross-provider deduplication
            diff_id = diff_ids[i] if i < len(diff_ids) else None
            if not diff_id:
                # Type narrowing for mypy
                layer_digest_str = str(layer_digest) if layer_digest else "unknown"
                image_digest_str = str(image_digest) if image_digest else "unknown"
                logger.warning(
                    f"Skipping layer {layer_digest_str[:16]}... at index {i} in image {image_digest_str[:16]}...: "
                    f"missing diff_id (config has {len(diff_ids)} diff_ids but manifest has {len(layers)} layers)"
                )
                skipped_layers_count += 1
                continue

            # Get or create layer entry keyed by diff_id for cross-provider deduplication
            if diff_id not in layers_by_diff_id:
                layers_by_diff_id[diff_id] = {
                    "diff_id": diff_id,
                    "digest": layer_digest,
                    "media_type": layer.get("mediaType"),
                    "size": layer.get("size"),
                    "next_diff_ids": set(),
                }

            layer_entry = layers_by_diff_id[diff_id]

            # Add NEXT relationship if not the last layer
            if i < len(layers) - 1:
                next_diff_id = diff_ids[i + 1] if i + 1 < len(diff_ids) else None
                if next_diff_id:
                    layer_entry["next_diff_ids"].add(next_diff_id)

    # Convert sets to lists for Neo4j ingestion
    all_layers = []
    for layer in layers_by_diff_id.values():
        layer_dict: dict[str, Any] = {
            "diff_id": layer["diff_id"],
            "digest": layer["digest"],
            "media_type": layer["media_type"],
            "size": layer["size"],
        }
        if layer["next_diff_ids"]:
            layer_dict["next_diff_ids"] = list(layer["next_diff_ids"])
        all_layers.append(layer_dict)

    logger.info(
        f"Transformed {len(all_layers)} container image layers with linked list structure"
    )

    if skipped_layers_count > 0:
        logger.warning(
            f"Skipped {skipped_layers_count} layer(s) due to missing digest or diff_id. "
            f"These layers will not appear in the graph. Check config blob availability."
        )

    return all_layers


@timeit
def load_container_images(
    neo4j_session: neo4j.Session,
    images: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    """
    Load container images into the graph.
    """
    load(
        neo4j_session,
        GitLabContainerImageSchema(),
        images,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def cleanup_container_images(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Clean up stale container images using the GraphJob framework.
    """
    GraphJob.from_node_schema(GitLabContainerImageSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def load_container_image_layers(
    neo4j_session: neo4j.Session,
    layers: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    """
    Load container image layers into the graph.
    """
    load(
        neo4j_session,
        GitLabContainerImageLayerSchema(),
        layers,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def cleanup_container_image_layers(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Clean up stale container image layers using the GraphJob framework.
    """
    GraphJob.from_node_schema(
        GitLabContainerImageLayerSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync_container_images(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    token: str,
    org_url: str,
    repositories: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Sync GitLab container images for an organization.

    Returns (manifests, manifest_lists) for use by attestations module.
    """
    raw_manifests, manifest_lists = get_container_images(
        gitlab_url, token, repositories
    )

    # Transform images and layers
    images = transform_container_images(raw_manifests)
    layers = transform_container_image_layers(raw_manifests)

    # Load layers FIRST so they exist when image relationships are created
    load_container_image_layers(neo4j_session, layers, org_url, update_tag)
    cleanup_container_image_layers(neo4j_session, common_job_parameters)

    # Load images (creates HAS_LAYER relationships to existing layer nodes)
    load_container_images(neo4j_session, images, org_url, update_tag)
    cleanup_container_images(neo4j_session, common_job_parameters)

    return raw_manifests, manifest_lists
