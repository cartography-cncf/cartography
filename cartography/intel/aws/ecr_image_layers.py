"""
ECR Image Layers module - fetches and syncs detailed container image layer information.

This is separate from the main ECR module to allow independent execution since layer
fetching can be significantly slower than basic ECR repository/image syncing.
"""

import asyncio
import logging
from typing import Any
from typing import Optional

import aioboto3
import httpx
import neo4j
from types_aiobotocore_ecr import ECRClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ecr_shared import ALL_ACCEPTED
from cartography.intel.aws.ecr_shared import (
    batch_get_manifest as shared_batch_get_manifest,
)
from cartography.intel.aws.ecr_shared import ECR_DOCKER_MANIFEST_MT
from cartography.intel.aws.ecr_shared import ECR_OCI_MANIFEST_MT
from cartography.intel.aws.ecr_shared import ECRFetchTransientError
from cartography.intel.aws.ecr_shared import (
    get_blob_json_via_presigned as shared_get_blob_json_via_presigned,
)
from cartography.intel.aws.ecr_shared import INDEX_MEDIA_TYPES_LOWER
from cartography.intel.container_arch import normalize_architecture
from cartography.models.aws.ecr.image import ECRImageSchema
from cartography.models.aws.ecr.image_layer import ECRImageLayerSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


ECRLayerFetchTransientError = ECRFetchTransientError


EMPTY_LAYER_DIFF_ID = (
    "sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef"
)

# Keep per-transaction memory low; each record fan-outs to many relationships.
ECR_LAYER_BATCH_SIZE = 200

# Media types that should be skipped when processing manifests
SKIP_CONFIG_MEDIA_TYPE_FRAGMENTS = {"buildkit", "attestation", "in-toto"}


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
    return await shared_batch_get_manifest(
        ecr_client,
        repo,
        image_ref,
        accepted_media_types,
    )


async def get_blob_json_via_presigned(
    ecr_client: ECRClient,
    repo: str,
    digest: str,
    http_client: httpx.AsyncClient,
) -> dict:
    return await shared_get_blob_json_via_presigned(
        ecr_client,
        repo,
        digest,
        http_client,
    )


async def _diff_ids_for_manifest(
    ecr_client: ECRClient,
    repo_name: str,
    manifest_doc: dict[str, Any],
    http_client: httpx.AsyncClient,
    platform_hint: Optional[str],
) -> tuple[dict[str, list[str]], dict[str, str]]:
    """
    Extract diff_ids and history from a manifest's config blob.

    Returns:
        - dict mapping platform to list of diff_ids
        - dict mapping diff_id to history command (created_by)
    """
    config = manifest_doc.get("config", {})
    config_media_type = config.get("mediaType", "").lower()

    # Skip certain media types
    if any(
        skip_fragment in config_media_type
        for skip_fragment in SKIP_CONFIG_MEDIA_TYPE_FRAGMENTS
    ):
        return {}, {}

    layers = manifest_doc.get("layers", [])
    if layers and all(
        "in-toto" in layer.get("mediaType", "").lower() for layer in layers
    ):
        return {}, {}

    cfg_digest = config.get("digest")
    if not cfg_digest:
        return {}, {}

    cfg_json = await get_blob_json_via_presigned(
        ecr_client,
        repo_name,
        cfg_digest,
        http_client,
    )
    if not cfg_json:
        return {}, {}

    # Docker API uses inconsistent casing - check for known variations
    rootfs = cfg_json.get("rootfs") or cfg_json.get("RootFS") or {}
    diff_ids = rootfs.get("diff_ids") or rootfs.get("DiffIDs") or []
    if not diff_ids:
        return {}, {}

    # Extract history and map to diff_ids
    # History entries with empty_layer=true don't have corresponding diff_ids
    history_list = cfg_json.get("history") or cfg_json.get("History") or []
    history_by_diff_id: dict[str, str] = {}

    diff_id_index = 0
    for hist_entry in history_list:
        is_empty_layer = hist_entry.get("empty_layer", False)
        if not is_empty_layer and diff_id_index < len(diff_ids):
            created_by = hist_entry.get("created_by", "")
            if created_by:
                history_by_diff_id[diff_ids[diff_id_index]] = created_by
            diff_id_index += 1

    if platform_hint:
        platform = platform_hint
    else:
        # Docker API uses inconsistent casing for platform components
        platform = _format_platform(
            cfg_json.get("os") or cfg_json.get("OS"),
            cfg_json.get("architecture") or cfg_json.get("Architecture"),
            cfg_json.get("variant") or cfg_json.get("Variant"),
        )

    return {platform: diff_ids}, history_by_diff_id


def transform_ecr_image_layers(
    image_layers_data: dict[str, dict[str, list[str]]],
    image_digest_map: dict[str, str],
    history_by_diff_id: Optional[dict[str, str]] = None,
    existing_properties_map: Optional[dict[str, dict[str, Any]]] = None,
) -> tuple[list[dict], list[dict]]:
    """
    Transform image layer data into format suitable for Neo4j ingestion.
    Creates linked list structure with NEXT relationships and HEAD/TAIL markers.

    :param image_layers_data: Map of image URI to platform to diff_ids
    :param image_digest_map: Map of image URI to image digest
    :param history_by_diff_id: Map of diff_id to history command (created_by)
    :param existing_properties_map: Map of image digest to existing ECRImage properties (type, architecture, etc.)
    :return: List of layer objects ready for ingestion
    """
    if history_by_diff_id is None:
        history_by_diff_id = {}
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
                if not membership.get("architecture"):
                    platform_values = list(platforms.keys())
                    if len(platform_values) == 1:
                        first_platform = platform_values[0]
                        arch_hint = (
                            first_platform.split("/")[1]
                            if "/" in first_platform
                            else first_platform
                        )
                        normalized_arch = normalize_architecture(arch_hint)
                        if normalized_arch != "unknown":
                            membership["architecture"] = normalized_arch
                    elif len(platform_values) > 1:
                        # Ambiguous platform hints for this digest; avoid arbitrary picks.
                        logger.debug(
                            "Skipping architecture backfill for %s due to multiple platform keys: %s",
                            image_digest,
                            platform_values,
                        )

            memberships_by_digest[image_digest] = membership

    # Convert sets back to lists for Neo4j ingestion
    layers = []
    for layer in layers_by_diff_id.values():
        diff_id = layer["diff_id"]
        layer_dict: dict[str, Any] = {
            "diff_id": diff_id,
            "is_empty": layer["is_empty"],
        }
        # Add history command if available
        if diff_id in history_by_diff_id:
            layer_dict["history"] = history_by_diff_id[diff_id]
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
) -> tuple[
    dict[str, dict[str, list[str]]],
    dict[str, str],
    dict[str, str],
]:
    """
    Fetch image layers for ECR images in parallel with caching and non-blocking I/O.

    Returns:
        - image_layers_data: Map of image URI to platform to diff_ids
        - image_digest_map: Map of image URI to image digest
        - history_by_diff_id: Map of diff_id to history command (created_by)
    """
    image_layers_data: dict[str, dict[str, list[str]]] = {}
    image_digest_map: dict[str, str] = {}
    all_history_by_diff_id: dict[str, str] = {}
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
    ) -> Optional[tuple[str, str, dict[str, list[str]], dict[str, str]]]:
        """
        Fetch layers for a single image.

        Returns tuple of (uri, digest, platform_layers, history_by_diff_id) or None.
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
            history_by_diff_id: dict[str, str] = {}

            if doc.get("manifests") and manifest_media_type in INDEX_MEDIA_TYPES_LOWER:

                async def _process_child_manifest(
                    manifest_ref: dict,
                ) -> tuple[dict[str, list[str]], dict[str, str]]:
                    # Skip attestation manifests — provenance is handled by ecr:provenance
                    if (
                        manifest_ref.get("annotations", {}).get(
                            "vnd.docker.reference.type"
                        )
                        == "attestation-manifest"
                    ):
                        return {}, {}

                    child_digest = manifest_ref.get("digest")
                    if not child_digest:
                        return {}, {}

                    # Use optimized caching for child manifest
                    child_doc, _ = await _fetch_and_cache_manifest(
                        repo_name,
                        child_digest,
                        [ECR_OCI_MANIFEST_MT, ECR_DOCKER_MANIFEST_MT],
                    )
                    if not child_doc:
                        return {}, {}

                    platform_hint = extract_platform_from_manifest(manifest_ref)
                    diff_map, history_map = await _diff_ids_for_manifest(
                        ecr_client,
                        repo_name,
                        child_doc,
                        http_client,
                        platform_hint,
                    )
                    return diff_map, history_map

                # Process all child manifests in parallel
                child_tasks = [
                    _process_child_manifest(manifest_ref)
                    for manifest_ref in doc.get("manifests", [])
                ]
                child_results = await asyncio.gather(
                    *child_tasks,
                    return_exceptions=True,
                )

                # Merge results from successful child manifest processing
                for result in child_results:
                    if isinstance(result, ECRLayerFetchTransientError):
                        logger.warning(
                            "Skipping child manifest after transient error: %s",
                            result,
                        )
                        continue
                    if isinstance(result, BaseException):
                        raise result
                    layer_data, hist_data = result
                    if layer_data:
                        platform_layers.update(layer_data)
                    if hist_data:
                        history_by_diff_id.update(hist_data)
            else:
                diff_map, hist_map = await _diff_ids_for_manifest(
                    ecr_client,
                    repo_name,
                    doc,
                    http_client,
                    None,
                )
                platform_layers.update(diff_map)
                history_by_diff_id.update(hist_map)

            if platform_layers:
                return (
                    uri,
                    digest,
                    platform_layers,
                    history_by_diff_id,
                )

            return None

    async with httpx.AsyncClient() as http_client:

        async def _fetch_single_image_layers_with_uri(
            repo_image: dict,
        ) -> tuple[
            str,
            Optional[tuple[str, str, dict[str, list[str]], dict[str, str]]],
        ]:
            try:
                return repo_image["uri"], await fetch_single_image_layers(
                    repo_image,
                    http_client,
                )
            except ECRLayerFetchTransientError as error:
                raise ECRLayerFetchTransientError(
                    f"{repo_image['uri']}: {error}"
                ) from error

        # Create tasks for all images
        tasks = [
            asyncio.create_task(
                _fetch_single_image_layers_with_uri(repo_image),
            )
            for repo_image in repo_images_list
        ]

        # Process with progress logging
        total = len(tasks)
        logger.info(
            f"Fetching layers for {total} images with {max_concurrent} concurrent connections..."
        )

        if not tasks:
            return (
                image_layers_data,
                image_digest_map,
                all_history_by_diff_id,
            )

        progress_interval = max(1, min(100, total // 10 or 1))
        completed = 0

        for task in asyncio.as_completed(tasks):
            try:
                _, result = await task
            except ECRLayerFetchTransientError as error:
                logger.warning(
                    "Skipping ECR layer extraction after transient failures were exhausted: %s",
                    error,
                    exc_info=True,
                )
                completed += 1
                if completed % progress_interval == 0 or completed == total:
                    percent = (completed / total) * 100
                    logger.info(
                        "Fetched layer metadata for %d/%d images (%.1f%%)",
                        completed,
                        total,
                        percent,
                    )
                continue
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
                uri, digest, layer_data, history_data = result
                if not digest:
                    raise ValueError(f"Empty digest returned for image {uri}")
                image_layers_data[uri] = layer_data
                image_digest_map[uri] = digest
                if history_data:
                    all_history_by_diff_id.update(history_data)

    logger.info(
        f"Successfully fetched layers for {len(image_layers_data)}/{len(repo_images_list)} images"
    )
    if all_history_by_diff_id:
        logger.info(
            f"Extracted history commands for {len(all_history_by_diff_id)} layers"
        )
    return (
        image_layers_data,
        image_digest_map,
        all_history_by_diff_id,
    )


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

        ecr_images = neo4j_session.execute_read(
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

                # Only fetch manifests for platform-specific images (layers).
                # Provenance is handled by ecr:provenance; attestations and manifest
                # lists have no useful layer data.
                if image_type == "image":
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
                dict[str, str],
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

            (
                image_layers_data,
                image_digest_map,
                history_by_diff_id,
            ) = loop.run_until_complete(_fetch_with_async_client())

            logger.info(
                f"Successfully fetched layers for {len(image_layers_data)} images"
            )
            layers, memberships = transform_ecr_image_layers(
                image_layers_data,
                image_digest_map,
                history_by_diff_id,
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
