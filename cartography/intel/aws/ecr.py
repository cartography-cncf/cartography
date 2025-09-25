import asyncio
import json
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import boto3
import httpx
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ecr.image import ECRImageSchema
from cartography.models.aws.ecr.image_layer import ImageLayerSchema
from cartography.models.aws.ecr.repository import ECRRepositorySchema
from cartography.models.aws.ecr.repository_image import ECRRepositoryImageSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit
from cartography.util import to_asynchronous
from cartography.util import to_synchronous

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_ecr_repositories(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict]:
    logger.info("Getting ECR repositories for region '%s'.", region)
    client = boto3_session.client("ecr", region_name=region)
    paginator = client.get_paginator("describe_repositories")
    ecr_repositories: List[Dict] = []
    for page in paginator.paginate():
        ecr_repositories.extend(page["repositories"])
    return ecr_repositories


@timeit
@aws_handle_regions
def get_ecr_repository_images(
    boto3_session: boto3.session.Session, region: str, repository_name: str
) -> List[Dict]:
    logger.debug(
        "Getting ECR images in repository '%s' for region '%s'.",
        repository_name,
        region,
    )
    client = boto3_session.client("ecr", region_name=region)
    list_paginator = client.get_paginator("list_images")
    ecr_repository_images: List[Dict] = []
    for page in list_paginator.paginate(repositoryName=repository_name):
        image_ids = page["imageIds"]
        if not image_ids:
            continue
        describe_paginator = client.get_paginator("describe_images")
        describe_response = describe_paginator.paginate(
            repositoryName=repository_name, imageIds=image_ids
        )
        for response in describe_response:
            image_details = response["imageDetails"]
            for detail in image_details:
                tags = detail.get("imageTags") or []
                if tags:
                    for tag in tags:
                        image_detail = {**detail, "imageTag": tag}
                        image_detail.pop("imageTags", None)
                        ecr_repository_images.append(image_detail)
                else:
                    ecr_repository_images.append({**detail})
    return ecr_repository_images


@timeit
def load_ecr_repositories(
    neo4j_session: neo4j.Session,
    repos: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading {len(repos)} ECR repositories for region {region} into graph.",
    )
    load(
        neo4j_session,
        ECRRepositorySchema(),
        repos,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def transform_ecr_repository_images(repo_data: Dict) -> List[Dict]:
    """
    Ensure that we only load ECRImage nodes to the graph if they have a defined imageDigest field.
    Process repositories in a consistent order to handle overlapping image digests deterministically.
    """
    repo_images_list = []
    # Sort repository URIs to ensure consistent processing order
    for repo_uri in sorted(repo_data.keys()):
        repo_images = repo_data[repo_uri]
        for img in repo_images:
            digest = img.get("imageDigest")
            if digest:
                tag = img.get("imageTag")
                uri = repo_uri + (f":{tag}" if tag else "")
                img["repo_uri"] = repo_uri
                img["uri"] = uri
                img["id"] = uri
                repo_images_list.append(img)
            else:
                logger.warning(
                    "Repo %s has an image that has no imageDigest. Its tag is %s. Continuing on.",
                    repo_uri,
                    img.get("imageTag"),
                )

    return repo_images_list


@timeit
def load_ecr_repository_images(
    neo4j_session: neo4j.Session,
    repo_images_list: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading {len(repo_images_list)} ECR repository images in {region} into graph.",
    )
    image_digests = {img["imageDigest"] for img in repo_images_list}
    ecr_images = [{"imageDigest": d} for d in image_digests]

    load(
        neo4j_session,
        ECRImageSchema(),
        ecr_images,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )

    load(
        neo4j_session,
        ECRRepositoryImageSchema(),
        repo_images_list,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


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
    """Parse ECR image URI into region, repository name, and reference (tag or digest)."""
    registry, rest = image_uri.split("/", 1)
    if "@sha256:" in rest:
        repo, ref = rest.split("@", 1)
    elif ":" in rest:
        repo, ref = rest.rsplit(":", 1)
    else:
        repo = rest
        ref = "latest"

    region = registry.split(".")[3]

    if ref.startswith("sha256:"):
        ref = f"sha256:{ref.split(':', 1)[1]}"

    return region, repo, ref


def batch_get_manifest(
    ecr_client: Any, repo: str, image_ref: str, accepted_media_types: List[str]
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
    ecr_client: Any,
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
    ecr_client: Any,
    repo_name: str,
    manifest_doc: Dict[str, Any],
    http_client: httpx.AsyncClient,
    platform_hint: Optional[str],
) -> Dict[str, List[str]]:
    config = manifest_doc.get("config") or {}
    config_media_type = (config.get("mediaType") or "").lower()

    if any(
        skip_fragment in config_media_type
        for skip_fragment in ("buildkit", "attestation", "in-toto")
    ):
        return {}

    layers = manifest_doc.get("layers") or []
    if layers and all(
        "in-toto" in (layer.get("mediaType") or "").lower() for layer in layers
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

    rootfs = cfg_json.get("rootfs") or cfg_json.get("RootFS") or {}
    diff_ids = rootfs.get("diff_ids") or rootfs.get("DiffIDs") or []
    if not diff_ids:
        return {}

    if platform_hint:
        platform = platform_hint
    else:
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
) -> List[Dict]:
    """
    Transform image layer data into format suitable for Neo4j ingestion.
    Creates linked list structure with NEXT relationships and HEAD/TAIL markers.

    :param image_layers_data: Map of image URI to platform to diff_ids
    :param image_digest_map: Map of image URI to image digest
    :return: List of layer objects ready for ingestion
    """
    layers: List[Dict[str, Any]] = []
    processed_diff_ids = set()

    for image_uri, platforms in sorted(image_layers_data.items()):
        image_digest = image_digest_map.get(image_uri)
        if not image_digest:
            logger.warning(f"No digest found for image {image_uri}")
            continue

        for platform, diff_ids in sorted(platforms.items()):
            if not diff_ids:
                continue

            # Process each layer in the chain
            for i, diff_id in enumerate(diff_ids):
                if diff_id not in processed_diff_ids:
                    layer: Dict[str, Any] = {"diff_id": diff_id}

                    # Add NEXT relationship if not the last layer
                    if i < len(diff_ids) - 1:
                        layer["next_diff_ids"] = [diff_ids[i + 1]]

                    # Track which images this layer is HEAD or TAIL of
                    if i == 0:
                        # This is the first layer (HEAD)
                        layer["head_image_ids"] = [image_digest]

                    if i == len(diff_ids) - 1:
                        # This is the last layer (TAIL)
                        layer["tail_image_ids"] = [image_digest]

                    layers.append(layer)
                    processed_diff_ids.add(diff_id)
                else:
                    # Layer already processed, update relationships
                    for layer in layers:
                        if layer["diff_id"] == diff_id:
                            # Add NEXT relationship if not the last layer
                            if i < len(diff_ids) - 1:
                                next_layer = diff_ids[i + 1]
                                existing_nexts = layer.get("next_diff_ids", [])
                                if next_layer not in existing_nexts:
                                    existing_nexts.append(next_layer)
                                    layer["next_diff_ids"] = existing_nexts

                            if i == 0:
                                existing_heads: Any = layer.get("head_image_ids", [])
                                if isinstance(existing_heads, list):
                                    if image_digest not in existing_heads:
                                        existing_heads.append(image_digest)
                                        layer["head_image_ids"] = existing_heads
                                else:
                                    layer["head_image_ids"] = [image_digest]
                            if i == len(diff_ids) - 1:
                                existing_tails: Any = layer.get("tail_image_ids", [])
                                if isinstance(existing_tails, list):
                                    if image_digest not in existing_tails:
                                        existing_tails.append(image_digest)
                                        layer["tail_image_ids"] = existing_tails
                                else:
                                    layer["tail_image_ids"] = [image_digest]
                            break

    return layers


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
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    logger.debug("Running ECR cleanup job.")
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


def _get_image_data(
    boto3_session: boto3.session.Session,
    region: str,
    repositories: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Given a list of repositories, get the image data for each repository,
    return as a mapping from repositoryUri to image object
    """
    image_data = {}

    async def async_get_images(repo: Dict[str, Any]) -> None:
        repo_image_obj = await to_asynchronous(
            get_ecr_repository_images,
            boto3_session,
            region,
            repo["repositoryName"],
        )
        image_data[repo["repositoryUri"]] = repo_image_obj

    # Sort repositories by name to ensure consistent processing order
    sorted_repos = sorted(repositories, key=lambda x: x["repositoryName"])
    to_synchronous(*[async_get_images(repo) for repo in sorted_repos])

    return image_data


async def fetch_image_layers_async(
    ecr_client: Any,
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

                manifest_media_type = (media_type or doc.get("mediaType") or "").lower()
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

                        child_doc, child_media_type = batch_get_manifest(
                            ecr_client,
                            repo_name,
                            child_digest,
                            [ECR_OCI_MANIFEST_MT, ECR_DOCKER_MANIFEST_MT],
                        )
                        if not child_doc:
                            continue

                        platform_info = manifest_ref.get("platform") or {}
                        platform_hint = _format_platform(
                            platform_info.get("os"),
                            platform_info.get("architecture"),
                            platform_info.get("variant"),
                        )

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


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info(
            "Syncing ECR for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        image_data = {}
        repositories = get_ecr_repositories(boto3_session, region)
        image_data = _get_image_data(boto3_session, region, repositories)
        # len here should be 1!
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

        # Fetch and load image layers
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
                layers = transform_ecr_image_layers(image_layers_data, image_digest_map)
                load_ecr_image_layers(
                    neo4j_session,
                    layers,
                    region,
                    current_aws_account_id,
                    update_tag,
                )
            else:
                logger.info("No image layers fetched")

    cleanup(neo4j_session, common_job_parameters)
