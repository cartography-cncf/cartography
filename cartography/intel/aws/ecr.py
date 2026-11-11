import json
import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.helpers import batch
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.container_arch import normalize_architecture
from cartography.models.aws.ecr.image import ECRImageBaseSchema
from cartography.models.aws.ecr.repository import ECRRepositorySchema
from cartography.models.aws.ecr.repository_image import ECRRepositoryImageSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit
from cartography.util import to_asynchronous
from cartography.util import to_synchronous

logger = logging.getLogger(__name__)

# Manifest list media types
MANIFEST_LIST_MEDIA_TYPES = {
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.index.v1+json",
}


REPO_BATCH_SIZE = 100
# API maximums for describe_images maxResults and batch_get_image imageIds.
DESCRIBE_IMAGES_PAGE_SIZE = 1000
BATCH_GET_IMAGE_MAX_IMAGE_IDS = 100


@timeit
@aws_handle_regions
def get_ecr_repositories(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict]:
    logger.debug("Getting ECR repositories for region '%s'.", region)
    client = create_boto3_client(boto3_session, "ecr", region_name=region)
    paginator = client.get_paginator("describe_repositories")
    ecr_repositories: List[Dict] = []
    for page in paginator.paginate():
        ecr_repositories.extend(page["repositories"])
    return ecr_repositories


def _parse_manifest_list(
    repository_name: str, manifest_list_digest: str, image_manifest: str
) -> List[Dict[str, Any]]:
    """
    Extract platform-specific images and attestations from a manifest list.
    """
    manifests = json.loads(image_manifest).get("manifests", [])

    if not manifests:
        raise ValueError(
            f"Manifest list {manifest_list_digest} has no manifests in repository {repository_name}"
        )

    all_images = []

    for manifest_ref in manifests:
        digest = manifest_ref.get("digest")
        if not digest:
            raise ValueError(
                f"Manifest in list {manifest_list_digest} has no digest in repository {repository_name}"
            )

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
                "architecture": (
                    normalize_architecture(architecture)
                    if architecture is not None
                    else None
                ),
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

    return all_images


def _get_manifest_list_images(
    client: Any, repository_name: str, manifest_list_digests: List[str]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Map each manifest list digest to its platform-specific images and attestations.

    Fetching many manifest lists per batch_get_image call matters at scale: modern
    BuildKit pushes an image index for nearly every build, so one call per manifest
    list made this the bulk of ECR API calls.

    A digest is absent from the result when batch_get_image returns no manifest list
    for it. describe_images can report a manifest list media type for single-platform
    images, which batch_get_image then omits because of the restrictive
    acceptedMediaTypes, and the caller treats those as regular images.
    """
    manifest_list_images: Dict[str, List[Dict[str, Any]]] = {}
    for digests in batch(manifest_list_digests, size=BATCH_GET_IMAGE_MAX_IMAGE_IDS):
        response = client.batch_get_image(
            repositoryName=repository_name,
            imageIds=[{"imageDigest": digest} for digest in digests],
            acceptedMediaTypes=list(MANIFEST_LIST_MEDIA_TYPES),
        )
        for image in response.get("images", []):
            digest = image["imageId"]["imageDigest"]
            manifest_list_images[digest] = _parse_manifest_list(
                repository_name, digest, image["imageManifest"]
            )

    for digest in manifest_list_digests:
        if digest not in manifest_list_images:
            logger.debug(
                "Digest %s in repository %s is not a manifest list despite media type hint",
                digest,
                repository_name,
            )
    return manifest_list_images


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
    client = create_boto3_client(boto3_session, "ecr", region_name=region)

    # Paging describe_images directly at its maximum page size replaces a
    # list_images call plus a describe_images call for every 100 image IDs.
    all_image_details: List[Dict] = []
    try:
        for page in client.get_paginator("describe_images").paginate(
            repositoryName=repository_name,
            PaginationConfig={"PageSize": DESCRIBE_IMAGES_PAGE_SIZE},
        ):
            all_image_details.extend(page["imageDetails"])

        manifest_list_images = _get_manifest_list_images(
            client,
            repository_name,
            [
                detail["imageDigest"]
                for detail in all_image_details
                if detail.get("imageManifestMediaType") in MANIFEST_LIST_MEDIA_TYPES
            ],
        )
    except client.exceptions.RepositoryNotFoundException:
        # The repository was deleted after describe_repositories listed it;
        # short-lived repositories (CI, integration tests) hit this race.
        logger.info(
            "ECR repository '%s' in region '%s' was deleted during sync; skipping its images.",
            repository_name,
            region,
        )
        return []
    # Track ALL digests so we don't create ECRRepositoryImages for them
    manifest_list_referenced_digests = {
        image["digest"] for images in manifest_list_images.values() for image in images
    }
    for detail in all_image_details:
        if detail["imageDigest"] in manifest_list_images:
            detail["_manifest_images"] = manifest_list_images[detail["imageDigest"]]

    # Only add images that should have AWSECRRepositoryImage nodes
    ecr_repository_images: List[Dict] = []
    for detail in all_image_details:
        tags = detail.get("imageTags") or []
        digest = detail.get("imageDigest")

        if tags:
            # Tagged images always get AWSECRRepositoryImage nodes (one per tag)
            for tag in tags:
                image_detail = {**detail, "imageTag": tag}
                image_detail.pop("imageTags", None)
                ecr_repository_images.append(image_detail)
        elif digest not in manifest_list_referenced_digests:
            # Untagged images only get nodes if they're NOT part of a manifest list
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
        - repo_images_list: List of AWSECRRepositoryImage nodes with imageDigests field (one-to-many)
        - ecr_images_list: List of AWSECRImage nodes with type, architecture, os, variant fields
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

            # Build AWSECRRepositoryImage node
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

                # Create AWSECRImage for the manifest list itself
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

                # Create AWSECRImage nodes for each image in the manifest list
                for manifest_img in manifest_images:
                    manifest_digest = manifest_img["digest"]
                    if manifest_digest not in ecr_images_dict:
                        ecr_images_dict[manifest_digest] = {
                            "imageDigest": manifest_digest,
                            "type": manifest_img.get("type"),
                            "architecture": (
                                normalize_architecture(manifest_img.get("architecture"))
                                if manifest_img.get("architecture") is not None
                                else None
                            ),
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

                # Create AWSECRImage for regular image
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
    GraphJob.from_node_schema(ECRImageBaseSchema(), common_job_parameters).run(
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
    for i in range(0, len(sorted_repos), REPO_BATCH_SIZE):
        batch = sorted_repos[i : i + REPO_BATCH_SIZE]
        to_synchronous(*[async_get_images(repo) for repo in batch])

    return image_data


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
        repo_images_list, ecr_images_list = transform_ecr_repository_images(image_data)
        load_ecr_repository_images(
            neo4j_session,
            repo_images_list,
            ecr_images_list,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup(neo4j_session, common_job_parameters)
