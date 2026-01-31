"""
GitHub Container Packages Intelligence Module

Syncs container packages from GitHub Container Registry (GHCR) into the graph.
Images are fetched via the Docker Registry V2 API to get full manifest details,
including architecture and OS information.
"""

import logging
import time
from typing import Any

import neo4j
import requests
from urllib.parse import urlparse

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.github import util
from cartography.models.github.container_images import GitHubContainerImageSchema
from cartography.models.github.container_package_tags import GitHubContainerPackageTagSchema
from cartography.models.github.container_packages import GitHubContainerPackageSchema
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
    ],
)

# Media types that indicate a manifest list (multi-arch image)
MANIFEST_LIST_MEDIA_TYPES = {
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.index.v1+json",
}

# Cache for registry JWT tokens
_registry_token_cache: dict[str, tuple[str, float]] = {}


def _get_ghcr_token(repository_name: str, token: str, force_refresh: bool = False) -> str:
    """
    Get a JWT token for accessing GHCR for a specific repository.
    """
    cache_key = repository_name
    if not force_refresh and cache_key in _registry_token_cache:
        cached_token, expiry_time = _registry_token_cache[cache_key]
        if time.time() < expiry_time - 60:
            return cached_token

    auth_url = "https://ghcr.io/token"
    params = {
        "service": "ghcr.io",
        "scope": f"repository:{repository_name}:pull",
    }
    # GitHub GHCR allows using PAT as the password in basic auth
    # Any username works, but "token" is a common convention
    response = requests.get(auth_url, params=params, auth=("token", token), timeout=30)
    response.raise_for_status()

    data = response.json()
    jwt_token = data.get("token")
    expires_in = data.get("expires_in", 3600)
    _registry_token_cache[cache_key] = (jwt_token, time.time() + expires_in)

    return jwt_token


def _fetch_manifest(repository_name: str, reference: str, token: str) -> requests.Response:
    """
    Fetch a manifest from GHCR with 401 retry handling.
    """
    jwt_token = _get_ghcr_token(repository_name, token)
    url = f"https://ghcr.io/v2/{repository_name}/manifests/{reference}"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": MANIFEST_ACCEPT_HEADER,
    }

    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code == 401:
        jwt_token = _get_ghcr_token(repository_name, token, force_refresh=True)
        headers["Authorization"] = f"Bearer {jwt_token}"
        response = requests.get(url, headers=headers, timeout=30)

    return response


def _fetch_config_blob(repository_name: str, blob_digest: str, token: str) -> dict[str, Any]:
    """
    Fetch a configuration blob from GHCR.
    """
    jwt_token = _get_ghcr_token(repository_name, token)
    url = f"https://ghcr.io/v2/{repository_name}/blobs/{blob_digest}"
    headers = {"Authorization": f"Bearer {jwt_token}"}

    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code == 401:
        jwt_token = _get_ghcr_token(repository_name, token, force_refresh=True)
        headers["Authorization"] = f"Bearer {jwt_token}"
        response = requests.get(url, headers=headers, timeout=30)

    response.raise_for_status()
    return response.json()


def get_container_packages(
    token: str,
    api_url: str,
    organization: str,
) -> list[dict[str, Any]]:
    """
    Fetch all container packages for a GitHub organization.
    """
    logger.info(f"Fetching container packages for organization {organization}")
    endpoint = f"/orgs/{organization}/packages?package_type=container"
    base_url = util._get_rest_api_base_url(api_url)

    packages = util.fetch_all_rest_api_pages(
        token,
        base_url,
        endpoint,
        result_key="",
    )

    logger.info(f"Fetched {len(packages)} container packages for {organization}")
    return packages


def get_package_versions(
    token: str,
    api_url: str,
    organization: str,
    package_name: str,
) -> list[dict[str, Any]]:
    """
    Fetch all versions for a specific container package.
    """
    endpoint = f"/orgs/{organization}/packages/container/{package_name}/versions"
    base_url = util._get_rest_api_base_url(api_url)

    versions = util.fetch_all_rest_api_pages(
        token,
        base_url,
        endpoint,
        result_key="",
    )

    return versions


def _get_image_manifest(repository_name: str, reference: str, token: str) -> dict[str, Any] | None:
    """
    Retrieve and parse manifest details for an image reference.
    """
    try:
        response = _fetch_manifest(repository_name, reference, token)
        if response.status_code == 404:
            return None
        response.raise_for_status()

        manifest = response.json()
        manifest["_digest"] = response.headers.get("Docker-Content-Digest") or reference
        manifest["_repository_name"] = repository_name
        manifest["_reference"] = reference

        return manifest
    except Exception as e:
        logger.warning(f"Failed to fetch manifest for {repository_name}:{reference}: {e}")
        return None


def get_container_images(
    token: str,
    api_url: str,
    organization: str,
    packages: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Fetch image manifests and metadata for all packages.
    Returns (manifests, tags).
    """
    all_manifests: list[dict[str, Any]] = []
    all_tags: list[dict[str, Any]] = []
    seen_digests: set[str] = set()

    for package in packages:
        package_name = package["name"]
        package_id = package["id"]
        # Repository name in registry is owner/package_name
        repository_name = f"{organization}/{package_name}".lower()

        versions = get_package_versions(token, api_url, organization, package_name)

        for version in versions:
            version_id = version["id"]
            # Typically for GHCR, the name of the version is the digest
            digest = version["name"]
            metadata = version.get("metadata", {}).get("container", {})
            tags = metadata.get("tags", [])

            # Fetch manifest for the version
            manifest = _get_image_manifest(repository_name, digest, token)
            if not manifest:
                continue

            # Process manifest
            if digest not in seen_digests:
                media_type = manifest.get("mediaType")
                is_manifest_list = media_type in MANIFEST_LIST_MEDIA_TYPES

                if is_manifest_list:
                    # Ingest manifest list itself
                    all_manifests.append(manifest)
                    seen_digests.add(digest)

                    # Fetch children
                    for child in manifest.get("manifests", []):
                        child_digest = child.get("digest")
                        if child_digest and child_digest not in seen_digests:
                            child_manifest = _get_image_manifest(repository_name, child_digest, token)
                            if child_manifest:
                                # Fetch config for platform info
                                config = child_manifest.get("config")
                                if config and config.get("digest"):
                                    try:
                                        child_manifest["_config"] = _fetch_config_blob(
                                            repository_name, config["digest"], token
                                        )
                                    except Exception:
                                        pass
                                all_manifests.append(child_manifest)
                                seen_digests.add(child_digest)
                else:
                    # Regular image
                    config = manifest.get("config")
                    if config and config.get("digest"):
                        try:
                            manifest["_config"] = _fetch_config_blob(repository_name, config["digest"], token)
                        except Exception:
                            pass
                    all_manifests.append(manifest)
                    seen_digests.add(digest)

            # Create tag nodes
            for tag_name in tags:
                all_tags.append({
                    "id": f"{package_name}:{tag_name}",
                    "name": tag_name,
                    "digest": digest,
                    "package_id": package_id,
                    "version_id": version_id,
                    "created_at": version.get("created_at"),
                    "updated_at": version.get("updated_at"),
                    "html_url": version.get("html_url"),
                })

    return all_manifests, all_tags


def transform_container_images(
    raw_manifests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Transform raw manifest data into graph format.
    """
    transformed = []
    for manifest in raw_manifests:
        media_type = manifest.get("mediaType")
        is_manifest_list = media_type in MANIFEST_LIST_MEDIA_TYPES
        config = manifest.get("_config", {})
        repository_name = manifest.get("_repository_name", "")

        child_image_digests = None
        if is_manifest_list:
            child_image_digests = [m.get("digest") for m in manifest.get("manifests", []) if m.get("digest")]

        transformed.append({
            "digest": manifest.get("_digest"),
            "uri": f"ghcr.io/{repository_name}",
            "media_type": media_type,
            "schema_version": manifest.get("schemaVersion"),
            "type": "manifest_list" if is_manifest_list else "image",
            "architecture": config.get("architecture"),
            "os": config.get("os"),
            "variant": config.get("variant"),
            "child_image_digests": child_image_digests,
        })
    return transformed


def transform_container_packages(
    raw_packages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Transform raw GitHub package data.
    """
    transformed = []
    for package in raw_packages:
        repository = package.get("repository")
        transformed.append({
            "id": package.get("id"),
            "name": package.get("name"),
            "package_type": package.get("package_type"),
            "visibility": package.get("visibility"),
            "url": package.get("url"),
            "html_url": package.get("html_url"),
            "created_at": package.get("created_at"),
            "updated_at": package.get("updated_at"),
            "owner_login": package.get("owner", {}).get("login"),
            "owner_type": package.get("owner", {}).get("type"),
            "repository_id": repository.get("id") if repository else None,
            "repository_name": repository.get("full_name") if repository else None,
        })
    return transformed


@timeit
def load_container_data(
    neo4j_session: neo4j.Session,
    packages: list[dict[str, Any]],
    images: list[dict[str, Any]],
    tags: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    """
    Load all GHCR data into the graph.
    """
    # Load Packages
    load(neo4j_session, GitHubContainerPackageSchema(), packages, lastupdated=update_tag, org_url=org_url)
    
    # Load Images
    load(neo4j_session, GitHubContainerImageSchema(), images, lastupdated=update_tag, org_url=org_url)
    
    # Load Tags
    load(neo4j_session, GitHubContainerPackageTagSchema(), tags, lastupdated=update_tag, org_url=org_url)


@timeit
def cleanup_container_data(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Cleanup GHCR data.
    """
    GraphJob.from_node_schema(GitHubContainerPackageSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(GitHubContainerImageSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(GitHubContainerPackageTagSchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync_container_packages(
    neo4j_session: neo4j.Session,
    token: str,
    api_url: str,
    organization: str,
    org_url: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Orchestrate GHCR sync.
    """
    logger.info(f"Syncing GHCR for organization {organization}")

    raw_packages = get_container_packages(token, api_url, organization)
    packages = transform_container_packages(raw_packages)

    raw_manifests, raw_tags = get_container_images(token, api_url, organization, raw_packages)
    images = transform_container_images(raw_manifests)

    load_container_data(neo4j_session, packages, images, raw_tags, org_url, update_tag)
    cleanup_container_data(neo4j_session, common_job_parameters)
