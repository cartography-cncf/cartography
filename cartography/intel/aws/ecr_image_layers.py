"""
ECR Image Layers module - fetches and syncs detailed container image layer information.

This is separate from the main ECR module to allow independent execution since layer
fetching can be significantly slower than basic ECR repository/image syncing.
"""

import asyncio
import json
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Protocol
from typing import Tuple

import boto3
import httpx
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ecr import _get_image_data
from cartography.intel.aws.ecr import get_ecr_repositories
from cartography.intel.aws.ecr import load_ecr_repositories
from cartography.intel.aws.ecr import load_ecr_repository_images
from cartography.intel.aws.ecr import transform_ecr_repository_images
from cartography.models.aws.ecr.image import ECRImageSchema
from cartography.models.aws.ecr.image_layer import ImageLayerSchema
from cartography.models.aws.ecr.repository import ECRRepositorySchema
from cartography.models.aws.ecr.repository_image import ECRRepositoryImageSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


# Constants
EMPTY_LAYER_DIFF_ID = (
    "sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef"
)

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


class ECRClient(Protocol):
    """Protocol for ECR client operations."""

    def batch_get_image(self, **kwargs: Any) -> Dict:
        """Get image manifest using batch_get_image API."""
        ...

    def get_download_url_for_layer(self, **kwargs: Any) -> Dict:
        """Get presigned URL for layer download."""
        ...


def extract_platform_from_manifest(manifest_ref: Dict) -> str:
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


def parse_image_uri(image_uri: str) -> Tuple[str, str, str]:
    """Parse ECR image URI into region, repository name, and reference (tag or digest).

    :param image_uri: ECR image URI in format: {account}.dkr.ecr.{region}.amazonaws.com/{repo}:{tag}
    :return: Tuple of (region, repository_name, reference)
    :raises ValueError: If the image URI is malformed
    """
    if not image_uri or "/" not in image_uri:
        raise ValueError(f"Invalid image URI format: {image_uri}")

    try:
        registry, rest = image_uri.split("/", 1)
    except ValueError:
        raise ValueError(f"Invalid image URI format: {image_uri}")

    # Parse registry to extract region
    registry_parts = registry.split(".")
    if len(registry_parts) < 6 or "ecr" not in registry_parts:
        raise ValueError(f"Invalid ECR registry format: {registry}")

    region = registry_parts[3]

    # Parse repository and reference (tag or digest)
    if "@sha256:" in rest:
        repo, ref = rest.split("@", 1)
    elif ":" in rest:
        repo, ref = rest.rsplit(":", 1)
    else:
        repo = rest
        ref = "latest"

    # Normalize sha256 references
    if ref.startswith("sha256:"):
        ref = f"sha256:{ref.split(':', 1)[1]}"

    return region, repo, ref


def batch_get_manifest(
    ecr_client: ECRClient, repo: str, image_ref: str, accepted_media_types: List[str]
) -> Tuple[Dict, str]:
    """Get image manifest using batch_get_image API."""
    try:
        resp = ecr_client.batch_get_image(
            repositoryName=repo,
            imageIds=(
                [{"imageDigest": image_ref}]
                if image_ref.startswith("sha256:")
                else [{"imageTag": image_ref}]
            ),
            acceptedMediaTypes=accepted_media_types,
        )
        if not resp.get("images"):
            logger.warning(f"No image found for {repo}:{image_ref}")
            return {}, ""
        manifest_json = json.loads(resp["images"][0]["imageManifest"])
        media_type = resp["images"][0].get("imageManifestMediaType", "")
        return manifest_json, media_type
    except Exception as e:
        logger.warning(f"Failed to get manifest for {repo}:{image_ref}: {e}")
        return {}, ""


async def get_blob_json_via_presigned(
    ecr_client: ECRClient,
    repo: str,
    digest: str,
    http_client: httpx.AsyncClient,
) -> Dict:
    """Download and parse JSON blob using presigned URL."""
    try:
        url_response = ecr_client.get_download_url_for_layer(
            repositoryName=repo,
            layerDigest=digest,
        )
        url = url_response["downloadUrl"]
        response = await http_client.get(url, timeout=30.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.debug(f"Failed to get blob {digest} for {repo}: {e}")
        return {}


async def _diff_ids_for_manifest(
    ecr_client: ECRClient,
    repo_name: str,
    manifest_doc: Dict[str, Any],
    http_client: httpx.AsyncClient,
    platform_hint: Optional[str],
) -> Dict[str, List[str]]:
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


@timeit
def transform_ecr_image_layers(
    image_layers_data: Dict[str, Dict[str, List[str]]],
    image_digest_map: Dict[str, str],
) -> Tuple[List[Dict], List[Dict]]:
    """
    Transform image layer data into format suitable for Neo4j ingestion.
    Creates linked list structure with NEXT relationships and HEAD/TAIL markers.

    :param image_layers_data: Map of image URI to platform to diff_ids
    :param image_digest_map: Map of image URI to image digest
    :return: List of layer objects ready for ingestion
    """
    layers_by_diff_id: Dict[str, Dict[str, Any]] = {}
    memberships: List[Dict[str, Any]] = []
    membership_keys: set[Tuple[str]] = set()

    for image_uri, platforms in sorted(image_layers_data.items()):
        image_digest = image_digest_map.get(image_uri)
        if not image_digest:
            logger.warning(f"No digest found for image {image_uri}")
            continue

        ordered_layers_for_image: Optional[List[str]] = None

        for _, diff_ids in sorted(platforms.items()):
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
            membership_key = (image_digest,)
            if membership_key not in membership_keys:
                memberships.append(
                    {
                        "imageDigest": image_digest,
                        "layer_diff_ids": ordered_layers_for_image,
                    }
                )
                membership_keys.add(membership_key)

    # Convert sets back to lists for Neo4j ingestion
    layers = []
    for layer in layers_by_diff_id.values():
        layer_dict: Dict[str, Any] = {
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

    return layers, memberships


@timeit
def load_ecr_image_layers(
    neo4j_session: neo4j.Session,
    image_layers: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """Load image layers into Neo4j."""
    if not image_layers:
        return

    logger.info(
        f"Loading {len(image_layers)} image layers for region {region} into graph.",
    )

    load(
        neo4j_session,
        ImageLayerSchema(),
        image_layers,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_ecr_image_layer_memberships(
    neo4j_session: neo4j.Session,
    memberships: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    if not memberships:
        return

    load(
        neo4j_session,
        ECRImageSchema(),
        memberships,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


async def fetch_image_layers_async(
    ecr_client: ECRClient,
    repo_images_list: List[Dict],
    max_concurrent: int = 20,
) -> Tuple[Dict[str, Dict[str, List[str]]], Dict[str, str]]:
    """
    Fetch image layers for ECR images in parallel.
    """
    image_layers_data = {}
    image_digest_map = {}
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_single_image_layers(
        repo_image: Dict,
        http_client: httpx.AsyncClient,
    ) -> Optional[Tuple[str, Dict[str, List[str]]]]:
        """Fetch layers for a single image."""
        async with semaphore:
            uri = repo_image.get("uri")
            digest = repo_image.get("imageDigest")
            repo_uri = repo_image.get("repo_uri")

            if not (uri and digest and repo_uri):
                return None

            try:
                # Extract repository name
                parts = repo_uri.split("/", 1)
                if len(parts) != 2:
                    return None
                repo_name = parts[1]

                # Get manifest
                doc, media_type = batch_get_manifest(
                    ecr_client,
                    repo_name,
                    digest,
                    ALL_ACCEPTED,
                )
                if not doc:
                    return None

                manifest_media_type = (media_type or doc.get("mediaType", "")).lower()
                platform_layers: Dict[str, List[str]] = {}

                if (
                    doc.get("manifests")
                    and manifest_media_type in INDEX_MEDIA_TYPES_LOWER
                ):
                    for manifest_ref in doc.get("manifests", []):
                        if (
                            manifest_ref.get("annotations", {}).get(
                                "vnd.docker.reference.type"
                            )
                            == "attestation-manifest"
                        ):
                            continue

                        child_digest = manifest_ref.get("digest")
                        if not child_digest:
                            continue

                        child_doc, _ = batch_get_manifest(
                            ecr_client,
                            repo_name,
                            child_digest,
                            [ECR_OCI_MANIFEST_MT, ECR_DOCKER_MANIFEST_MT],
                        )
                        if not child_doc:
                            continue

                        platform_hint = extract_platform_from_manifest(manifest_ref)

                        diff_map = await _diff_ids_for_manifest(
                            ecr_client,
                            repo_name,
                            child_doc,
                            http_client,
                            platform_hint,
                        )
                        platform_layers.update(diff_map)
                else:
                    diff_map = await _diff_ids_for_manifest(
                        ecr_client,
                        repo_name,
                        doc,
                        http_client,
                        None,
                    )
                    platform_layers.update(diff_map)

                if platform_layers:
                    return uri, platform_layers

                return None

            except Exception as e:
                logger.debug(f"Could not get layers for {uri}: {e}")
                return None

    async with httpx.AsyncClient() as http_client:
        # Create tasks for all images
        tasks = [
            fetch_single_image_layers(repo_image, http_client)
            for repo_image in repo_images_list
        ]

        # Process with progress logging
        total = len(tasks)
        logger.info(
            f"Fetching layers for {total} images with {max_concurrent} concurrent connections..."
        )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(results):
            if (
                result
                and not isinstance(result, Exception)
                and isinstance(result, tuple)
            ):
                uri, layer_data = result
                image_layers_data[uri] = layer_data
                # Get digest from original list
                digest = repo_images_list[i].get("imageDigest")
                if digest:
                    image_digest_map[uri] = digest

    logger.info(
        f"Successfully fetched layers for {len(image_layers_data)}/{len(repo_images_list)} images"
    )
    return image_layers_data, image_digest_map


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """Run ECR cleanup including image layer cleanup."""
    logger.debug("Running ECR cleanup job including image layers.")
    GraphJob.from_node_schema(ECRRepositorySchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(ECRRepositoryImageSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(ECRImageSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(ImageLayerSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Sync ECR image layers. This fetches detailed layer information for all ECR images.

    Note: This also syncs basic ECR repositories and images to ensure data consistency.
    Layer fetching can be slow for accounts with many container images.
    """

    for region in regions:
        logger.info(
            "Syncing ECR image layers for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )

        # First sync basic ECR data (repositories and images)
        repositories = get_ecr_repositories(boto3_session, region)
        image_data = _get_image_data(boto3_session, region, repositories)

        load_ecr_repositories(
            neo4j_session,
            repositories,
            region,
            current_aws_account_id,
            update_tag,
        )

        repo_images_list = transform_ecr_repository_images(image_data)
        load_ecr_repository_images(
            neo4j_session,
            repo_images_list,
            region,
            current_aws_account_id,
            update_tag,
        )

        # Now fetch and load image layers
        ecr_client = boto3_session.client("ecr", region_name=region)

        if repo_images_list:
            logger.info(
                f"Starting to fetch layers for {len(repo_images_list)} images..."
            )
            image_layers_data, image_digest_map = asyncio.run(
                fetch_image_layers_async(ecr_client, repo_images_list)
            )

            if image_layers_data:
                logger.info(
                    f"Successfully fetched layers for {len(image_layers_data)} images"
                )
                layers, memberships = transform_ecr_image_layers(
                    image_layers_data,
                    image_digest_map,
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
            else:
                logger.info("No image layers fetched")

    cleanup(neo4j_session, common_job_parameters)
