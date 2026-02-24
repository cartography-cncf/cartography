import asyncio
import json
import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import List

import aioboto3
import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.async_runtime import AwsAsyncTuning
from cartography.intel.aws.util.async_runtime import build_aio_config
from cartography.intel.aws.util.async_runtime import run_async
from cartography.models.aws.ecr.image import ECRImageBaseSchema
from cartography.models.aws.ecr.image import ECRImageSchema
from cartography.models.aws.ecr.repository import ECRRepositorySchema
from cartography.models.aws.ecr.repository_image import ECRRepositoryImageSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Manifest list media types
MANIFEST_LIST_MEDIA_TYPES = {
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.index.v1+json",
}

ECR_LIST_PAGE_SIZE = 1000


def _iter_in_batches(
    items: List[Dict[str, Any]],
    batch_size: int,
) -> Generator[List[Dict[str, Any]], None, None]:
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


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


async def _get_ecr_repositories_async(
    aioboto3_session: aioboto3.Session,
    region: str,
    tuning: AwsAsyncTuning,
) -> List[Dict[str, Any]]:
    repositories: List[Dict[str, Any]] = []
    next_token: str | None = None
    aio_config = build_aio_config(tuning)
    async with aioboto3_session.client(
        "ecr",
        region_name=region,
        config=aio_config,
    ) as client:
        while True:
            params: Dict[str, Any] = {"maxResults": ECR_LIST_PAGE_SIZE}
            if next_token:
                params["nextToken"] = next_token
            response = await client.describe_repositories(**params)
            repositories.extend(response.get("repositories", []))
            next_token = response.get("nextToken")
            if not next_token:
                break
    return repositories


def _get_platform_specific_digests(
    client: Any, repository_name: str, manifest_list_digest: str
) -> tuple[List[Dict[str, Any]], set[str]]:
    """
    Fetch manifest list and extract platform-specific image digests and attestations.

    Returns:
        - List of all images (platform-specific + attestations) with digest, type, architecture, os, variant
        - Set of ALL digests referenced in the manifest list
    """
    response = client.batch_get_image(
        repositoryName=repository_name,
        imageIds=[{"imageDigest": manifest_list_digest}],
        acceptedMediaTypes=list(MANIFEST_LIST_MEDIA_TYPES),
    )

    if not response.get("images"):
        # Image is not actually a manifest list despite the media type hint.
        # This can happen with single-platform images where describe_images reports
        # a manifest list media type but batch_get_image with restrictive acceptedMediaTypes
        # returns empty results. Return empty results so caller treats it as a regular image.
        logger.debug(
            "Digest %s in repository %s is not a manifest list despite media type hint",
            manifest_list_digest,
            repository_name,
        )
        return [], set()

    # batch_get_image returns a single manifest list (hence [0])
    # The manifests[] array inside contains all platform-specific images and attestations
    manifest_json = json.loads(response["images"][0]["imageManifest"])
    manifests = manifest_json.get("manifests", [])

    if not manifests:
        raise ValueError(
            f"Manifest list {manifest_list_digest} has no manifests in repository {repository_name}"
        )

    all_images = []
    all_referenced_digests = set()

    for manifest_ref in manifests:
        digest = manifest_ref.get("digest")
        if not digest:
            raise ValueError(
                f"Manifest in list {manifest_list_digest} has no digest in repository {repository_name}"
            )

        all_referenced_digests.add(digest)

        platform_info = manifest_ref.get("platform", {})
        architecture = platform_info.get("architecture")
        os_name = platform_info.get("os")

        # Determine if this is an attestation
        annotations = manifest_ref.get("annotations", {})
        is_attestation = (
            architecture == "unknown" and os_name == "unknown"
        ) or annotations.get("vnd.docker.reference.type") == "attestation-manifest"

        all_images.append(
            {
                "digest": digest,
                "type": "attestation" if is_attestation else "image",
                "architecture": architecture,
                "os": os_name,
                "variant": platform_info.get("variant"),
                "attestation_type": (
                    annotations.get("vnd.docker.reference.type")
                    if is_attestation
                    else None
                ),
                "attests_digest": (
                    annotations.get("vnd.docker.reference.digest")
                    if is_attestation
                    else None
                ),
                "media_type": manifest_ref.get("mediaType"),
                "artifact_media_type": manifest_ref.get("artifactType"),
            }
        )

    return all_images, all_referenced_digests


async def _get_platform_specific_digests_async(
    client: Any,
    repository_name: str,
    manifest_list_digest: str,
) -> tuple[List[Dict[str, Any]], set[str]]:
    response = await client.batch_get_image(
        repositoryName=repository_name,
        imageIds=[{"imageDigest": manifest_list_digest}],
        acceptedMediaTypes=list(MANIFEST_LIST_MEDIA_TYPES),
    )
    if not response.get("images"):
        logger.debug(
            "Digest %s in repository %s is not a manifest list despite media type hint",
            manifest_list_digest,
            repository_name,
        )
        return [], set()

    manifest_json = json.loads(response["images"][0]["imageManifest"])
    manifests = manifest_json.get("manifests", [])
    if not manifests:
        raise ValueError(
            f"Manifest list {manifest_list_digest} has no manifests in repository {repository_name}"
        )

    all_images: List[Dict[str, Any]] = []
    all_referenced_digests: set[str] = set()
    for manifest_ref in manifests:
        digest = manifest_ref.get("digest")
        if not digest:
            raise ValueError(
                f"Manifest in list {manifest_list_digest} has no digest in repository {repository_name}"
            )
        all_referenced_digests.add(digest)
        platform_info = manifest_ref.get("platform", {})
        architecture = platform_info.get("architecture")
        os_name = platform_info.get("os")
        annotations = manifest_ref.get("annotations", {})
        is_attestation = (
            architecture == "unknown" and os_name == "unknown"
        ) or annotations.get("vnd.docker.reference.type") == "attestation-manifest"
        all_images.append(
            {
                "digest": digest,
                "type": "attestation" if is_attestation else "image",
                "architecture": architecture,
                "os": os_name,
                "variant": platform_info.get("variant"),
                "attestation_type": (
                    annotations.get("vnd.docker.reference.type")
                    if is_attestation
                    else None
                ),
                "attests_digest": (
                    annotations.get("vnd.docker.reference.digest")
                    if is_attestation
                    else None
                ),
                "media_type": manifest_ref.get("mediaType"),
                "artifact_media_type": manifest_ref.get("artifactType"),
            }
        )
    return all_images, all_referenced_digests


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

    # First pass: Collect all image details and track manifest list referenced digests
    all_image_details: List[Dict] = []
    manifest_list_referenced_digests: set[str] = set()

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
                # Check if this is a manifest list
                media_type = detail.get("imageManifestMediaType")
                if media_type in MANIFEST_LIST_MEDIA_TYPES:
                    # Fetch all images from manifest list (platform-specific + attestations)
                    manifest_list_digest = detail["imageDigest"]
                    manifest_images, all_digests = _get_platform_specific_digests(
                        client, repository_name, manifest_list_digest
                    )
                    detail["_manifest_images"] = manifest_images

                    # Track ALL digests so we don't create ECRRepositoryImages for them
                    manifest_list_referenced_digests.update(all_digests)

                all_image_details.append(detail)

    # Second pass: Only add images that should have ECRRepositoryImage nodes
    ecr_repository_images: List[Dict] = []
    for detail in all_image_details:
        tags = detail.get("imageTags") or []
        digest = detail.get("imageDigest")

        if tags:
            # Tagged images always get ECRRepositoryImage nodes (one per tag)
            for tag in tags:
                image_detail = {**detail, "imageTag": tag}
                image_detail.pop("imageTags", None)
                ecr_repository_images.append(image_detail)
        elif digest not in manifest_list_referenced_digests:
            # Untagged images only get nodes if they're NOT part of a manifest list
            ecr_repository_images.append({**detail})

    return ecr_repository_images


async def _get_ecr_repository_images_async(
    client: Any,
    repository_name: str,
) -> List[Dict[str, Any]]:
    all_image_details: List[Dict[str, Any]] = []
    manifest_list_referenced_digests: set[str] = set()
    list_next_token: str | None = None

    while True:
        list_params: Dict[str, Any] = {
            "repositoryName": repository_name,
            "maxResults": ECR_LIST_PAGE_SIZE,
        }
        if list_next_token:
            list_params["nextToken"] = list_next_token
        page = await client.list_images(**list_params)
        image_ids = page.get("imageIds", [])
        list_next_token = page.get("nextToken")
        if not image_ids:
            if not list_next_token:
                break
            continue

        for i in range(0, len(image_ids), 100):
            batch_ids = image_ids[i : i + 100]
            response = await client.describe_images(
                repositoryName=repository_name,
                imageIds=batch_ids,
            )
            image_details = response.get("imageDetails", [])
            for detail in image_details:
                media_type = detail.get("imageManifestMediaType")
                if media_type in MANIFEST_LIST_MEDIA_TYPES:
                    manifest_list_digest = detail["imageDigest"]
                    manifest_images, all_digests = (
                        await _get_platform_specific_digests_async(
                            client,
                            repository_name,
                            manifest_list_digest,
                        )
                    )
                    detail["_manifest_images"] = manifest_images
                    manifest_list_referenced_digests.update(all_digests)
                all_image_details.append(detail)

        if not list_next_token:
            break

    ecr_repository_images: List[Dict[str, Any]] = []
    for detail in all_image_details:
        tags = detail.get("imageTags") or []
        digest = detail.get("imageDigest")
        if tags:
            for tag in tags:
                image_detail = {**detail, "imageTag": tag}
                image_detail.pop("imageTags", None)
                ecr_repository_images.append(image_detail)
        elif digest not in manifest_list_referenced_digests:
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
def transform_ecr_repository_images(repo_data: Dict) -> tuple[List[Dict], List[Dict]]:
    """
    Transform ECR repository images into repo image list and ECR image list.
    For manifest lists, creates ECR images for manifest list, platform-specific images, and attestations.

    Returns:
        - repo_images_list: List of ECRRepositoryImage nodes with imageDigests field (one-to-many)
        - ecr_images_list: List of ECRImage nodes with type, architecture, os, variant fields
    """
    repo_images_list = []
    ecr_images_dict: Dict[str, Dict] = {}  # Deduplicate by digest

    # Sort repository URIs to ensure consistent processing order
    for repo_uri in sorted(repo_data.keys()):
        repo_images = repo_data[repo_uri]
        for img in repo_images:
            digest = img.get("imageDigest")
            if not digest:
                logger.warning(
                    "Repo %s has an image that has no imageDigest. Its tag is %s. Continuing on.",
                    repo_uri,
                    img.get("imageTag"),
                )
                continue

            tag = img.get("imageTag")
            uri = repo_uri + (f":{tag}" if tag else "")

            # Build ECRRepositoryImage node
            repo_image = {
                **img,
                "repo_uri": repo_uri,
                "uri": uri,
                "id": uri,
            }

            # Check if this is a manifest list with images
            manifest_images = img.get("_manifest_images")
            if manifest_images:
                # For manifest list: include manifest list digest + all referenced digests
                all_digests = [digest] + [m["digest"] for m in manifest_images]
                repo_image["imageDigests"] = all_digests

                # Create ECRImage for the manifest list itself
                if digest not in ecr_images_dict:
                    # Extract child image digests (excluding attestations for CONTAINS_IMAGE relationship)
                    child_digests = [
                        m["digest"]
                        for m in manifest_images
                        if m.get("type") != "attestation"
                    ]
                    ecr_images_dict[digest] = {
                        "imageDigest": digest,
                        "type": "manifest_list",
                        "architecture": None,
                        "os": None,
                        "variant": None,
                        "child_image_digests": child_digests if child_digests else None,
                    }

                # Create ECRImage nodes for each image in the manifest list
                for manifest_img in manifest_images:
                    manifest_digest = manifest_img["digest"]
                    if manifest_digest not in ecr_images_dict:
                        ecr_images_dict[manifest_digest] = {
                            "imageDigest": manifest_digest,
                            "type": manifest_img.get("type"),
                            "architecture": manifest_img.get("architecture"),
                            "os": manifest_img.get("os"),
                            "variant": manifest_img.get("variant"),
                            "attestation_type": manifest_img.get("attestation_type"),
                            "attests_digest": manifest_img.get("attests_digest"),
                            "media_type": manifest_img.get("media_type"),
                            "artifact_media_type": manifest_img.get(
                                "artifact_media_type"
                            ),
                        }
            else:
                # Regular image: single digest
                repo_image["imageDigests"] = [digest]

                # Create ECRImage for regular image
                if digest not in ecr_images_dict:
                    ecr_images_dict[digest] = {
                        "imageDigest": digest,
                        "type": "image",
                        "architecture": None,
                        "os": None,
                        "variant": None,
                    }

            # Remove internal field before returning
            repo_image.pop("_manifest_images", None)
            repo_images_list.append(repo_image)

    ecr_images_list = list(ecr_images_dict.values())
    return repo_images_list, ecr_images_list


@timeit
def load_ecr_repository_images(
    neo4j_session: neo4j.Session,
    repo_images_list: List[Dict],
    ecr_images_list: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading {len(ecr_images_list)} ECR images and {len(repo_images_list)} ECR repository images in {region} into graph.",
    )

    load(
        neo4j_session,
        ECRImageBaseSchema(),
        ecr_images_list,
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


async def _get_image_data_async(
    aioboto3_session: aioboto3.Session,
    region: str,
    repositories: List[Dict[str, Any]],
    tuning: AwsAsyncTuning,
) -> Dict[str, Any]:
    """
    Given a list of repositories, get the image data for each repository,
    return as a mapping from repositoryUri to image object
    """
    image_data: Dict[str, Any] = {}
    semaphore = asyncio.Semaphore(tuning.max_concurrent_repositories)
    aio_config = build_aio_config(tuning)

    async with aioboto3_session.client(
        "ecr",
        region_name=region,
        config=aio_config,
    ) as client:

        async def _fetch_one(repo: Dict[str, Any]) -> tuple[str, List[Dict[str, Any]]]:
            async with semaphore:
                images = await _get_ecr_repository_images_async(
                    client,
                    repo["repositoryName"],
                )
            return repo["repositoryUri"], images

        for i in range(0, len(repositories), tuning.max_concurrent_repositories):
            batch = repositories[i : i + tuning.max_concurrent_repositories]
            batch_results = await asyncio.gather(*[_fetch_one(repo) for repo in batch])
            for repo_uri, repo_images in batch_results:
                image_data[repo_uri] = repo_images
    # Sort repositories by name to ensure consistent processing order
    # Sort repositories by name to ensure consistent processing order
    image_data = dict(sorted(image_data.items()))
    return image_data


def _get_image_data_sync(
    boto3_session: boto3.session.Session,
    region: str,
    repositories: List[Dict[str, Any]],
) -> Dict[str, Any]:
    image_data: Dict[str, Any] = {}
    sorted_repos = sorted(repositories, key=lambda x: x["repositoryName"])
    for repo in sorted_repos:
        image_data[repo["repositoryUri"]] = get_ecr_repository_images(
            boto3_session,
            region,
            repo["repositoryName"],
        )
    return dict(sorted(image_data.items()))


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
    aioboto3_session: aioboto3.Session | None = None,
) -> None:
    use_async = aioboto3_session is not None
    tuning = AwsAsyncTuning.from_env()
    for region in regions:
        logger.info(
            "Syncing ECR for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        if use_async:
            repositories = run_async(
                _get_ecr_repositories_async(aioboto3_session, region, tuning),
            )
        else:
            repositories = get_ecr_repositories(boto3_session, region)

        sorted_repositories = sorted(repositories, key=lambda x: x["repositoryName"])
        # len here should be 1!
        load_ecr_repositories(
            neo4j_session,
            repositories,
            region,
            current_aws_account_id,
            update_tag,
        )
        seen_image_digests: set[str] = set()
        for repo_batch in _iter_in_batches(
            sorted_repositories,
            tuning.max_concurrent_repositories,
        ):
            if use_async:
                image_data = run_async(
                    _get_image_data_async(
                        aioboto3_session,
                        region,
                        repo_batch,
                        tuning,
                    )
                )
            else:
                image_data = _get_image_data_sync(boto3_session, region, repo_batch)

            repo_images_list, ecr_images_list = transform_ecr_repository_images(
                image_data
            )
            new_ecr_images = []
            for image in ecr_images_list:
                digest = image["imageDigest"]
                if digest in seen_image_digests:
                    continue
                seen_image_digests.add(digest)
                new_ecr_images.append(image)
            load_ecr_repository_images(
                neo4j_session,
                repo_images_list,
                new_ecr_images,
                region,
                current_aws_account_id,
                update_tag,
            )
    cleanup(neo4j_session, common_job_parameters)
