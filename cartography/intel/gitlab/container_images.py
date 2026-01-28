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

        # Extract architecture, os, variant from config blob (for regular images)
        config = manifest.get("_config", {})

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
            }
        )

    logger.info(f"Transformed {len(transformed)} container images")
    return transformed


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
    images = transform_container_images(raw_manifests)
    load_container_images(neo4j_session, images, org_url, update_tag)
    cleanup_container_images(neo4j_session, common_job_parameters)
    return raw_manifests, manifest_lists
