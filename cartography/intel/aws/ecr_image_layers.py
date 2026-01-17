"""
ECR Image Layers module - fetches and syncs detailed container image layer information.

This is separate from the main ECR module to allow independent execution since layer
fetching can be significantly slower than basic ECR repository/image syncing.
"""

import asyncio
import json
import logging
from typing import Any
from typing import Optional

import aioboto3
import httpx
import neo4j
from botocore.exceptions import ClientError
from types_aiobotocore_ecr import ECRClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ecr.image import ECRImageSchema
from cartography.models.aws.ecr.image_layer import ECRImageLayerSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


EMPTY_LAYER_DIFF_ID = (
    "sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef"
)

# Keep per-transaction memory low; each record fan-outs to many relationships.
ECR_LAYER_BATCH_SIZE = 200

# ECR manifest media types
ECR_DOCKER_INDEX_MT = "application/vnd.docker.distribution.manifest.list.v2+json"
ECR_DOCKER_MANIFEST_MT = "application/vnd.docker.distribution.manifest.v2+json"
ECR_OCI_INDEX_MT = "application/vnd.oci.image.index.v1+json"
ECR_OCI_MANIFEST_MT = "application/vnd.oci.image.manifest.v1+json"

ALL_ACCEPTED = [
    ECR_OCI_INDEX_MT,
    ECR_DOCKER_INDEX_MT,
    ECR_OCI_MANIFEST_MT,
    ECR_DOCKER_MANIFEST_MT,
]

INDEX_MEDIA_TYPES = {ECR_OCI_INDEX_MT, ECR_DOCKER_INDEX_MT}
INDEX_MEDIA_TYPES_LOWER = {mt.lower() for mt in INDEX_MEDIA_TYPES}

# Media types that should be skipped when processing manifests
SKIP_CONFIG_MEDIA_TYPE_FRAGMENTS = {"buildkit", "attestation", "in-toto"}


def extract_repo_uri_from_image_uri(image_uri: str) -> str:
    """
    Extract repository URI from image URI by removing tag or digest.

    Examples:
        "repo@sha256:digest" -> "repo"
        "repo:tag" -> "repo"
        "repo" -> "repo"
    """
    if "@sha256:" in image_uri:
        return image_uri.split("@", 1)[0]
    elif ":" in image_uri:
        return image_uri.rsplit(":", 1)[0]
    else:
        return image_uri


def extract_platform_from_manifest(manifest_ref: dict) -> str:
    """Extract platform string from manifest reference."""
    platform_info = manifest_ref.get("platform", {})
    return _format_platform(
        platform_info.get("os"),
        platform_info.get("architecture"),
        platform_info.get("variant"),
    )


def _format_platform(
    os_name: Optional[str],
    architecture: Optional[str],
    variant: Optional[str] = None,
) -> str:
    components = [os_name or "unknown", architecture or "unknown"]
    if variant:
        components.append(variant)
    return "/".join(components)


async def batch_get_manifest(
    ecr_client: ECRClient, repo: str, image_ref: str, accepted_media_types: list[str]
) -> tuple[dict, str]:
    """Get image manifest using batch_get_image API."""
    try:
        resp = await ecr_client.batch_get_image(
            repositoryName=repo,
            imageIds=(
                [{"imageDigest": image_ref}]
                if image_ref.startswith("sha256:")
                else [{"imageTag": image_ref}]
            ),
            acceptedMediaTypes=accepted_media_types,
        )
    except ClientError as error:
        error_code = error.response.get("Error", {}).get("Code", "")
        if error_code == "ImageNotFoundException":
            logger.warning(
                "Image %s:%s not found while fetching manifest", repo, image_ref
            )
            return {}, ""
        # Fail loudly on throttling or unexpected AWS errors
        logger.error(
            "Failed to get manifest for %s:%s due to AWS error %s",
            repo,
            image_ref,
            error_code,
        )
        raise
    except Exception:
        logger.exception(
            "Unexpected error fetching manifest for %s:%s", repo, image_ref
        )
        raise

    if not resp.get("images"):
        logger.warning(f"No image found for {repo}:{image_ref}")
        return {}, ""

    manifest_json = json.loads(resp["images"][0]["imageManifest"])
    media_type = resp["images"][0].get("imageManifestMediaType", "")
    return manifest_json, media_type


async def get_blob_json_via_presigned(
    ecr_client: ECRClient,
    repo: str,
    digest: str,
    http_client: httpx.AsyncClient,
) -> dict:
    """Download and parse JSON blob using presigned URL."""
    try:
        url_response = await ecr_client.get_download_url_for_layer(
            repositoryName=repo,
            layerDigest=digest,
        )
    except ClientError as error:
        logger.error(
            "Failed to request download URL for layer %s in repo %s: %s",
            digest,
            repo,
            error.response.get("Error", {}).get("Code", "unknown"),
        )
        raise

    url = url_response["downloadUrl"]
    try:
        response = await http_client.get(url, timeout=30.0)
        response.raise_for_status()
    except httpx.HTTPError as error:
        logger.error(
            "HTTP error downloading blob %s for repo %s: %s",
            digest,
            repo,
            error,
        )
        raise

    return response.json()


async def _extract_parent_image_from_attestation(
    ecr_client: ECRClient,
    repo_name: str,
    attestation_manifest_digest: str,
    http_client: httpx.AsyncClient,
) -> Optional[dict[str, str]]:
    """
    Extract parent image information from an in-toto provenance attestation.

    This function fetches an attestation manifest, downloads its in-toto layer,
    and extracts the parent image reference from the SLSA provenance materials.

    :param ecr_client: ECR client for fetching manifests and layers
    :param repo_name: ECR repository name
    :param attestation_manifest_digest: Digest of the attestation manifest
    :param http_client: HTTP client for downloading blobs
    :return: Dict with parent_image_uri and parent_image_digest, or None if no parent image found
    """
    try:
        attestation_manifest, _ = await batch_get_manifest(
            ecr_client,
            repo_name,
            attestation_manifest_digest,
            [ECR_OCI_MANIFEST_MT, ECR_DOCKER_MANIFEST_MT],
        )

        if not attestation_manifest:
            logger.debug(
                "No attestation manifest found for digest %s in repo %s",
                attestation_manifest_digest,
                repo_name,
            )
            return None

        # Get the in-toto layer from the attestation manifest
        layers = attestation_manifest.get("layers", [])
        intoto_layer = next(
            (
                layer
                for layer in layers
                if "in-toto" in layer.get("mediaType", "").lower()
            ),
            None,
        )

        if not intoto_layer:
            logger.debug(
                "No in-toto layer found in attestation manifest %s",
                attestation_manifest_digest,
            )
            return None

        # Download the in-toto attestation blob
        intoto_digest = intoto_layer.get("digest")
        if not intoto_digest:
            logger.debug("No digest found for in-toto layer")
            return None

        attestation_blob = await get_blob_json_via_presigned(
            ecr_client,
            repo_name,
            intoto_digest,
            http_client,
        )

        if not attestation_blob:
            logger.debug("Failed to download attestation blob")
            return None

        # Extract parent image from SLSA provenance materials
        materials = attestation_blob.get("predicate", {}).get("materials", [])
        for material in materials:
            uri = material.get("uri", "")
            uri_l = uri.lower()
            # Look for container image URIs that are NOT the dockerfile itself
            is_container_ref = (
                uri_l.startswith("pkg:docker/")
                or uri_l.startswith("pkg:oci/")
                or uri_l.startswith("oci://")
            )
            if is_container_ref and "dockerfile" not in uri_l:
                digest_obj = material.get("digest", {})
                sha256_digest = digest_obj.get("sha256")
                if sha256_digest:
                    return {
                        "parent_image_uri": uri,
                        "parent_image_digest": f"sha256:{sha256_digest}",
                    }

        logger.debug(
            "No parent image found in attestation materials for %s",
            attestation_manifest_digest,
        )
        return None

    except Exception as e:
        logger.warning(
            "Error extracting parent image from attestation %s in repo %s: %s",
            attestation_manifest_digest,
            repo_name,
            e,
        )
        return None


async def _diff_ids_for_manifest(
    ecr_client: ECRClient,
    repo_name: str,
    manifest_doc: dict[str, Any],
    http_client: httpx.AsyncClient,
    platform_hint: Optional[str],
) -> dict[str, list[str]]:
    config = manifest_doc.get("config", {})
    config_media_type = config.get("mediaType", "").lower()

    # Skip certain media types
    if any(
        skip_fragment in config_media_type
        for skip_fragment in SKIP_CONFIG_MEDIA_TYPE_FRAGMENTS
    ):
        return {}

    layers = manifest_doc.get("layers", [])
    if layers and all(
        "in-toto" in layer.get("mediaType", "").lower() for layer in layers
    ):
        return {}

    cfg_digest = config.get("digest")
    if not cfg_digest:
        return {}

    cfg_json = await get_blob_json_via_presigned(
        ecr_client,
        repo_name,
        cfg_digest,
        http_client,
    )
    if not cfg_json:
        return {}

    # Docker API uses inconsistent casing - check for known variations
    rootfs = cfg_json.get("rootfs") or cfg_json.get("RootFS") or {}
    diff_ids = rootfs.get("diff_ids") or rootfs.get("DiffIDs") or []
    if not diff_ids:
        return {}

    if platform_hint:
        platform = platform_hint
    else:
        # Docker API uses inconsistent casing for platform components
        platform = _format_platform(
            cfg_json.get("os") or cfg_json.get("OS"),
            cfg_json.get("architecture") or cfg_json.get("Architecture"),
            cfg_json.get("variant") or cfg_json.get("Variant"),
        )

    return {platform: diff_ids}


def transform_ecr_image_layers(
    image_layers_data: dict[str, dict[str, list[str]]],
    image_digest_map: dict[str, str],
    image_attestation_map: Optional[dict[str, dict[str, str]]] = None,
    existing_properties_map: Optional[dict[str, dict[str, Any]]] = None,
) -> tuple[list[dict], list[dict]]:
    """
    Transform image layer data into format suitable for Neo4j ingestion.
    Creates linked list structure with NEXT relationships and HEAD/TAIL markers.

    :param image_layers_data: Map of image URI to platform to diff_ids
    :param image_digest_map: Map of image URI to image digest
    :param image_attestation_map: Map of image URI to attestation data (parent_image_uri, parent_image_digest)
    :param existing_properties_map: Map of image digest to existing ECRImage properties (type, architecture, etc.)
    :return: List of layer objects ready for ingestion
    """
    if image_attestation_map is None:
        image_attestation_map = {}
    if existing_properties_map is None:
        existing_properties_map = {}
    layers_by_diff_id: dict[str, dict[str, Any]] = {}
    memberships_by_digest: dict[str, dict[str, Any]] = {}

    for image_uri, platforms in image_layers_data.items():
        # fetch_image_layers_async guarantees every uri in image_layers_data has a digest
        image_digest = image_digest_map[image_uri]

        # Check if this is a manifest list
        is_manifest_list = False
        if image_digest in existing_properties_map:
            image_type = existing_properties_map[image_digest].get("type")
            is_manifest_list = image_type == "manifest_list"

        # Skip creating layer relationships for manifest lists
        if is_manifest_list:
            continue

        ordered_layers_for_image: Optional[list[str]] = None

        for _, diff_ids in platforms.items():
            if not diff_ids:
                continue

            if ordered_layers_for_image is None:
                ordered_layers_for_image = list(diff_ids)

            # Process each layer in the chain
            for i, diff_id in enumerate(diff_ids):
                # Get or create layer
                if diff_id not in layers_by_diff_id:
                    layers_by_diff_id[diff_id] = {
                        "diff_id": diff_id,
                        "is_empty": diff_id == EMPTY_LAYER_DIFF_ID,
                        "next_diff_ids": set(),
                        "head_image_ids": set(),
                        "tail_image_ids": set(),
                    }

                layer = layers_by_diff_id[diff_id]

                # Add NEXT relationship if not the last layer
                if i < len(diff_ids) - 1:
                    layer["next_diff_ids"].add(diff_ids[i + 1])

                # Track which images this layer is HEAD or TAIL of
                if i == 0:
                    layer["head_image_ids"].add(image_digest)
                if i == len(diff_ids) - 1:
                    layer["tail_image_ids"].add(image_digest)

        if ordered_layers_for_image:
            membership: dict[str, Any] = {
                "layer_diff_ids": ordered_layers_for_image,
            }

            # Preserve existing ECRImage properties (type, architecture, os, variant, etc.)
            if image_digest in existing_properties_map:
                membership.update(existing_properties_map[image_digest])

            # Add attestation data if available for this image
            if image_uri in image_attestation_map:
                attestation = image_attestation_map[image_uri]
                membership["parent_image_uri"] = attestation["parent_image_uri"]
                membership["parent_image_digest"] = attestation["parent_image_digest"]
                membership["from_attestation"] = True
                membership["confidence"] = "explicit"

            memberships_by_digest[image_digest] = membership

    # Convert sets back to lists for Neo4j ingestion
    layers = []
    for layer in layers_by_diff_id.values():
        layer_dict: dict[str, Any] = {
            "diff_id": layer["diff_id"],
            "is_empty": layer["is_empty"],
        }
        if layer["next_diff_ids"]:
            layer_dict["next_diff_ids"] = list(layer["next_diff_ids"])
        if layer["head_image_ids"]:
            layer_dict["head_image_ids"] = list(layer["head_image_ids"])
        if layer["tail_image_ids"]:
            layer_dict["tail_image_ids"] = list(layer["tail_image_ids"])
        layers.append(layer_dict)

    # Reconstruct memberships list with imageDigest field
    memberships = [
        {"imageDigest": digest, **membership_data}
        for digest, membership_data in memberships_by_digest.items()
    ]

    return layers, memberships


@timeit
def load_ecr_image_layers(
    neo4j_session: neo4j.Session,
    image_layers: list[dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load image layers into Neo4j.

    Uses a conservative batch size (ECR_LAYER_LOAD_BATCH_SIZE) to avoid Neo4j
    transaction memory limits, since layer objects can contain large arrays of
    relationships.
    """
    logger.info(
        f"Loading {len(image_layers)} image layers for region {region} into graph.",
    )

    load(
        neo4j_session,
        ECRImageLayerSchema(),
        image_layers,
        batch_size=ECR_LAYER_BATCH_SIZE,
        lastupdated=aws_update_tag,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_ecr_image_layer_memberships(
    neo4j_session: neo4j.Session,
    memberships: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load image layer memberships into Neo4j.

    Uses a conservative batch size (ECR_LAYER_MEMBERSHIP_BATCH_SIZE) to avoid
    Neo4j transaction memory limits, since membership objects can contain large
    arrays of layer diff_ids.
    """
    load(
        neo4j_session,
        ECRImageSchema(),
        memberships,
        batch_size=ECR_LAYER_BATCH_SIZE,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


async def fetch_image_layers_async(
    ecr_client: ECRClient,
    repo_images_list: list[dict],
    max_concurrent: int = 200,
) -> tuple[dict[str, dict[str, list[str]]], dict[str, str], dict[str, dict[str, str]]]:
    """
    Fetch image layers for ECR images in parallel with caching and non-blocking I/O.

    Returns:
        - image_layers_data: Map of image URI to platform to diff_ids
        - image_digest_map: Map of image URI to image digest
        - image_attestation_map: Map of image URI to attestation data (parent_image_uri, parent_image_digest)
    """
    image_layers_data: dict[str, dict[str, list[str]]] = {}
    image_digest_map: dict[str, str] = {}
    image_attestation_map: dict[str, dict[str, str]] = {}
    semaphore = asyncio.Semaphore(max_concurrent)

    # Cache for manifest fetches keyed by (repo_name, imageDigest)
    manifest_cache: dict[tuple[str, str], tuple[dict, str]] = {}
    # Lock for thread-safe cache access
    cache_lock = asyncio.Lock()
    # In-flight requests to coalesce duplicate fetches
    inflight: dict[tuple[str, str], asyncio.Task] = {}

    async def _fetch_and_cache_manifest(
        repo_name: str, digest_or_tag: str, accepted: list[str]
    ) -> tuple[dict, str]:
        """
        Fetch and cache manifest with double-checked locking and in-flight coalescing.
        """
        key = (repo_name, digest_or_tag)

        # Fast path: check cache without lock
        if key in manifest_cache:
            return manifest_cache[key]

        # Check for existing in-flight request
        task = inflight.get(key)
        if task is None:
            # Create new task for this manifest
            async def _do() -> tuple[dict, str]:
                # Fetch without holding the lock
                doc, mt = await batch_get_manifest(
                    ecr_client, repo_name, digest_or_tag, accepted
                )
                # Store result under lock (second check to avoid races)
                async with cache_lock:
                    return manifest_cache.setdefault(key, (doc, mt))

            task = asyncio.create_task(_do())
            inflight[key] = task

        try:
            return await task
        finally:
            # Clean up inflight entry
            inflight.pop(key, None)

    async def fetch_single_image_layers(
        repo_image: dict,
        http_client: httpx.AsyncClient,
    ) -> Optional[
        tuple[str, str, dict[str, list[str]], Optional[dict[str, dict[str, str]]]]
    ]:
        """
        Fetch layers for a single image and extract attestation if present.

        Returns tuple of (uri, digest, platform_layers, attestations_by_child_digest) where
        attestations_by_child_digest maps child image digest to parent image info
        """
        async with semaphore:
            # Caller guarantees these fields exist in every repo_image
            uri = repo_image["uri"]
            digest = repo_image["imageDigest"]
            repo_uri = repo_image["repo_uri"]

            # Extract repository name
            parts = repo_uri.split("/", 1)
            if len(parts) != 2:
                raise ValueError(f"Unexpected ECR repository URI format: {repo_uri}")
            repo_name = parts[1]

            # Get manifest using optimized caching
            doc, media_type = await _fetch_and_cache_manifest(
                repo_name, digest, ALL_ACCEPTED
            )

            if not doc:
                return None

            manifest_media_type = (media_type or doc.get("mediaType", "")).lower()
            platform_layers: dict[str, list[str]] = {}
            attestation_data: Optional[dict[str, dict[str, str]]] = None

            if doc.get("manifests") and manifest_media_type in INDEX_MEDIA_TYPES_LOWER:

                async def _process_child_manifest(
                    manifest_ref: dict,
                ) -> tuple[dict[str, list[str]], Optional[tuple[str, dict[str, str]]]]:
                    # Check if this is an attestation manifest
                    if (
                        manifest_ref.get("annotations", {}).get(
                            "vnd.docker.reference.type"
                        )
                        == "attestation-manifest"
                    ):
                        # Extract which child image this attestation is for
                        attests_child_digest = manifest_ref.get("annotations", {}).get(
                            "vnd.docker.reference.digest"
                        )
                        if not attests_child_digest:
                            return {}, None

                        # Extract base image from attestation
                        attestation_digest = manifest_ref.get("digest")
                        if attestation_digest:
                            attestation_info = (
                                await _extract_parent_image_from_attestation(
                                    ecr_client,
                                    repo_name,
                                    attestation_digest,
                                    http_client,
                                )
                            )
                            if attestation_info:
                                # Return (attests_child_digest, parent_info) tuple
                                return {}, (attests_child_digest, attestation_info)
                        return {}, None

                    child_digest = manifest_ref.get("digest")
                    if not child_digest:
                        return {}, None

                    # Use optimized caching for child manifest
                    child_doc, _ = await _fetch_and_cache_manifest(
                        repo_name,
                        child_digest,
                        [ECR_OCI_MANIFEST_MT, ECR_DOCKER_MANIFEST_MT],
                    )
                    if not child_doc:
                        return {}, None

                    platform_hint = extract_platform_from_manifest(manifest_ref)
                    diff_map = await _diff_ids_for_manifest(
                        ecr_client,
                        repo_name,
                        child_doc,
                        http_client,
                        platform_hint,
                    )
                    return diff_map, None

                # Process all child manifests in parallel
                child_tasks = [
                    _process_child_manifest(manifest_ref)
                    for manifest_ref in doc.get("manifests", [])
                ]
                child_results = await asyncio.gather(
                    *child_tasks, return_exceptions=True
                )

                # Merge results from successful child manifest processing
                # Track attestation data by child digest for proper mapping
                attestations_by_child_digest: dict[str, dict[str, str]] = {}

                for result in child_results:
                    if isinstance(result, tuple) and len(result) == 2:
                        layer_data, attest_data = result
                        if layer_data:
                            platform_layers.update(layer_data)
                        if attest_data:
                            # attest_data is (child_digest, parent_info) tuple
                            child_digest, parent_info = attest_data
                            attestations_by_child_digest[child_digest] = parent_info

                # Build attestation_data with child digest mapping
                if attestations_by_child_digest:
                    attestation_data = attestations_by_child_digest
            else:
                diff_map = await _diff_ids_for_manifest(
                    ecr_client,
                    repo_name,
                    doc,
                    http_client,
                    None,
                )
                platform_layers.update(diff_map)

            # Return if we found layers or attestation data
            # Manifest lists may have attestation_data without platform_layers
            if platform_layers or attestation_data:
                return uri, digest, platform_layers, attestation_data

            return None

    async with httpx.AsyncClient() as http_client:
        # Create tasks for all images
        tasks = [
            asyncio.create_task(
                fetch_single_image_layers(repo_image, http_client),
            )
            for repo_image in repo_images_list
        ]

        # Process with progress logging
        total = len(tasks)
        logger.info(
            f"Fetching layers for {total} images with {max_concurrent} concurrent connections..."
        )

        if not tasks:
            return image_layers_data, image_digest_map, image_attestation_map

        progress_interval = max(1, min(100, total // 10 or 1))
        completed = 0

        for task in asyncio.as_completed(tasks):
            result = await task
            completed += 1

            if completed % progress_interval == 0 or completed == total:
                percent = (completed / total) * 100
                logger.info(
                    "Fetched layer metadata for %d/%d images (%.1f%%)",
                    completed,
                    total,
                    percent,
                )

            if result:
                uri, digest, layer_data, attestations_by_child_digest = result
                if not digest:
                    raise ValueError(f"Empty digest returned for image {uri}")
                image_layers_data[uri] = layer_data
                image_digest_map[uri] = digest
                if attestations_by_child_digest:
                    # Map attestation data by child digest URIs
                    repo_uri = extract_repo_uri_from_image_uri(uri)
                    for (
                        child_digest,
                        parent_info,
                    ) in attestations_by_child_digest.items():
                        child_uri = f"{repo_uri}@{child_digest}"
                        image_attestation_map[child_uri] = parent_info
                        # Also add to digest map so transform can look up the child digest
                        image_digest_map[child_uri] = child_digest

    logger.info(
        f"Successfully fetched layers for {len(image_layers_data)}/{len(repo_images_list)} images"
    )
    if image_attestation_map:
        logger.info(
            f"Found attestations with base image info for {len(image_attestation_map)} images"
        )
    return image_layers_data, image_digest_map, image_attestation_map


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    logger.debug("Running image layer cleanup job.")
    GraphJob.from_node_schema(ECRImageLayerSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    aioboto3_session: aioboto3.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Sync ECR image layers. This fetches detailed layer information for ECR images
    that already exist in the graph.

    Prerequisites: Basic ECR data (repositories and images) must already be loaded
    via the 'ecr' module before running this.

    Layer fetching can be slow for accounts with many container images.
    """

    for region in regions:
        logger.info(
            "Syncing ECR image layers for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )

        # Query for ECR images with all their existing properties to preserve during layer sync
        query = """
        MATCH (img:ECRImage)<-[:IMAGE]-(repo_img:ECRRepositoryImage)<-[:REPO_IMAGE]-(repo:ECRRepository)
        MATCH (repo)<-[:RESOURCE]-(:AWSAccount {id: $AWS_ID})
        WHERE repo.region = $Region
        RETURN DISTINCT
            img.digest AS digest,
            repo_img.id AS uri,
            repo.uri AS repo_uri,
            img.type AS type,
            img.architecture AS architecture,
            img.os AS os,
            img.variant AS variant,
            img.attestation_type AS attestation_type,
            img.attests_digest AS attests_digest,
            img.media_type AS media_type,
            img.artifact_media_type AS artifact_media_type,
            img.child_image_digests AS child_image_digests
        """
        from cartography.client.core.tx import read_list_of_dicts_tx

        ecr_images = neo4j_session.read_transaction(
            read_list_of_dicts_tx, query, AWS_ID=current_aws_account_id, Region=region
        )

        # Build repo_images_list and existing_properties map
        repo_images_list = []
        existing_properties = {}
        seen_digests = set()

        for img_data in ecr_images:
            digest = img_data["digest"]
            image_type = img_data.get("type")

            if digest not in seen_digests:
                seen_digests.add(digest)

                # Store existing properties for ALL images to preserve during updates
                existing_properties[digest] = {
                    "type": image_type,
                    "architecture": img_data.get("architecture"),
                    "os": img_data.get("os"),
                    "variant": img_data.get("variant"),
                    "attestation_type": img_data.get("attestation_type"),
                    "attests_digest": img_data.get("attests_digest"),
                    "media_type": img_data.get("media_type"),
                    "artifact_media_type": img_data.get("artifact_media_type"),
                    "child_image_digests": img_data.get("child_image_digests"),
                }

                repo_uri = img_data["repo_uri"]
                digest_uri = f"{repo_uri}@{digest}"

                # Fetch manifests for:
                # - Platform-specific images (type="image") - to get their layers
                # - Manifest lists (type="manifest_list") - to extract attestation parent image data
                # Skip only attestations since they don't have useful layer or parent data
                if image_type != "attestation":
                    repo_images_list.append(
                        {
                            "imageDigest": digest,
                            "uri": digest_uri,
                            "repo_uri": repo_uri,
                        }
                    )

        logger.info(
            f"Found {len(repo_images_list)} distinct ECR image digests in graph for region {region}"
        )

        if not repo_images_list:
            logger.warning(
                f"No ECR images found in graph for region {region}. "
                f"Run 'ecr' sync first to populate basic ECR data."
            )
            continue

        # Fetch and load image layers using async ECR client
        if repo_images_list:
            logger.info(
                f"Starting to fetch layers for {len(repo_images_list)} images..."
            )

            async def _fetch_with_async_client() -> tuple[
                dict[str, dict[str, list[str]]],
                dict[str, str],
                dict[str, dict[str, str]],
            ]:
                async with aioboto3_session.client(
                    "ecr", region_name=region
                ) as ecr_client:
                    return await fetch_image_layers_async(ecr_client, repo_images_list)

            # Use get_event_loop() + run_until_complete() to avoid tearing down loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # No event loop in current thread, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            image_layers_data, image_digest_map, image_attestation_map = (
                loop.run_until_complete(_fetch_with_async_client())
            )

            logger.info(
                f"Successfully fetched layers for {len(image_layers_data)} images"
            )
            layers, memberships = transform_ecr_image_layers(
                image_layers_data,
                image_digest_map,
                image_attestation_map,
                existing_properties,
            )
            load_ecr_image_layers(
                neo4j_session,
                layers,
                region,
                current_aws_account_id,
                update_tag,
            )
            load_ecr_image_layer_memberships(
                neo4j_session,
                memberships,
                region,
                current_aws_account_id,
                update_tag,
            )

    cleanup(neo4j_session, common_job_parameters)
