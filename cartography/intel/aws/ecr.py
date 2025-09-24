import json
import logging
import urllib.request
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import boto3
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


def get_blob_json_via_presigned(ecr_client: Any, repo: str, digest: str) -> Dict:
    """Download and parse JSON blob using presigned URL."""
    try:
        url_response = ecr_client.get_download_url_for_layer(
            repositoryName=repo,
            layerDigest=digest,
        )
        url = url_response["downloadUrl"]
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        logger.warning(f"Failed to get blob {digest} for {repo}: {e}")
        return {}


def diff_ids_from_manifest(ecr_client: Any, repo: str, manifest_doc: Dict) -> List[str]:
    """Extract diff_ids from an image manifest by fetching its config blob."""
    if not manifest_doc or "config" not in manifest_doc:
        return []

    config = manifest_doc["config"]
    cfg_digest = config.get("digest")
    if not cfg_digest:
        return []

    # Skip BuildKit cache manifests and other non-image configs
    cfg_media_type = config.get("mediaType", "")
    if "buildkit" in cfg_media_type.lower():
        logger.debug(f"Skipping BuildKit cache manifest for {repo}")
        return []

    cfg_json = get_blob_json_via_presigned(ecr_client, repo, cfg_digest)
    if not cfg_json:
        return []

    rootfs = cfg_json.get("rootfs") or cfg_json.get("RootFS") or {}
    return rootfs.get("diff_ids") or rootfs.get("DiffIDs") or []


def get_image_diff_ids_by_digest(
    ecr_client: Any,
    repo_name: str,
    image_digest: str,
    prefer_platform: Optional[str] = "linux/amd64",
) -> Dict[str, List[str]]:
    """
    Get diff_ids for an ECR image using its digest directly.
    This is more reliable than using tags which may change or not exist.
    Returns a dict mapping platform strings to lists of diff_ids.
    """
    # Get manifest using digest
    doc, mt = batch_get_manifest(ecr_client, repo_name, image_digest, ALL_ACCEPTED)
    if not doc:
        return {}

    # Helper to stringify platform keys
    def plat_key(m: Dict) -> str:
        p = m.get("platform", {}) or {}
        os_, arch, var = p.get("os"), p.get("architecture"), p.get("variant")
        if os_ and arch:
            return f"{os_}/{arch}" + (f"/{var}" if var else "")
        return "unknown/unknown"

    # If it's an index (OCI or Docker), walk into each manifest
    if (mt in (ECR_OCI_INDEX_MT, ECR_DOCKER_INDEX_MT)) or ("manifests" in doc):
        results: Dict[str, List[str]] = {}
        manifests = []
        for m in doc.get("manifests", []):
            # Skip attestations
            if (m.get("annotations") or {}).get(
                "vnd.docker.reference.type"
            ) == "attestation-manifest":
                continue
            manifests.append(m)

        # Optional: prioritize prefer_platform first
        def score(m: Dict) -> int:
            k = plat_key(m)
            return 0 if prefer_platform and k == prefer_platform else 1

        for m in sorted(manifests, key=score):
            digest = m.get("digest")
            if not digest:
                continue
            plat_manifest, plat_mt = batch_get_manifest(
                ecr_client,
                repo_name,
                digest,
                [ECR_OCI_MANIFEST_MT, ECR_DOCKER_MANIFEST_MT],
            )
            if plat_mt not in (ECR_OCI_MANIFEST_MT, ECR_DOCKER_MANIFEST_MT):
                continue
            diffs = diff_ids_from_manifest(ecr_client, repo_name, plat_manifest)
            if diffs:
                results[plat_key(m)] = diffs
        return results

    # Otherwise, it's a single (platform-specific) manifest
    diffs = diff_ids_from_manifest(ecr_client, repo_name, doc)
    return {prefer_platform or "linux/amd64": diffs} if diffs else {}


def get_image_diff_ids(
    ecr_client: Any,
    image_uri: str,
    prefer_platform: Optional[str] = "linux/amd64",
) -> Dict[str, List[str]]:
    """
    Get diff_ids for an ECR image, handling both single-platform and multi-arch images.
    Returns a dict mapping platform strings to lists of diff_ids.
    """
    try:
        region, repo, ref = parse_image_uri(image_uri)
    except Exception as e:
        logger.warning(f"Failed to parse image URI {image_uri}: {e}")
        return {}

    # Get manifest (could be index or single manifest)
    doc, mt = batch_get_manifest(ecr_client, repo, ref, ALL_ACCEPTED)
    if not doc:
        return {}

    # Helper to stringify platform keys
    def plat_key(m: Dict) -> str:
        p = m.get("platform", {}) or {}
        os_, arch, var = p.get("os"), p.get("architecture"), p.get("variant")
        if os_ and arch:
            return f"{os_}/{arch}" + (f"/{var}" if var else "")
        return "unknown/unknown"

    # If it's an index (OCI or Docker), walk into each manifest
    if (mt in (ECR_OCI_INDEX_MT, ECR_DOCKER_INDEX_MT)) or ("manifests" in doc):
        results: Dict[str, List[str]] = {}
        manifests = []
        for m in doc.get("manifests", []):
            # Skip attestations
            if (m.get("annotations") or {}).get(
                "vnd.docker.reference.type"
            ) == "attestation-manifest":
                continue
            manifests.append(m)

        # Optional: prioritize prefer_platform first
        def score(m: Dict) -> int:
            k = plat_key(m)
            return 0 if prefer_platform and k == prefer_platform else 1

        for m in sorted(manifests, key=score):
            digest = m.get("digest")
            if not digest:
                continue
            plat_manifest, plat_mt = batch_get_manifest(
                ecr_client,
                repo,
                digest,
                [ECR_OCI_MANIFEST_MT, ECR_DOCKER_MANIFEST_MT],
            )
            if plat_mt not in (ECR_OCI_MANIFEST_MT, ECR_DOCKER_MANIFEST_MT):
                continue
            diffs = diff_ids_from_manifest(ecr_client, repo, plat_manifest)
            if diffs:
                results[plat_key(m)] = diffs
        return results

    # Otherwise, it's a single (platform-specific) manifest
    diffs = diff_ids_from_manifest(ecr_client, repo, doc)
    return {prefer_platform or "linux/amd64": diffs} if diffs else {}


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
                        layer["next_diff_id"] = diff_ids[i + 1]

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
                    # Layer already processed, but may need to update HEAD/TAIL relationships
                    for layer in layers:
                        if layer["diff_id"] == diff_id:
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
        image_layers_data = {}
        image_digest_map = {}

        for repo_image in repo_images_list:
            uri = repo_image.get("uri")
            digest = repo_image.get("imageDigest")
            repo_uri = repo_image.get("repo_uri")

            if uri and digest and repo_uri:
                image_digest_map[uri] = digest
                try:
                    # Extract repository name from repo_uri
                    # repo_uri format: registry.region.amazonaws.com/repo-name
                    parts = repo_uri.split("/", 1)
                    if len(parts) == 2:
                        repo_name = parts[1]
                    else:
                        logger.warning(
                            f"Could not parse repository name from {repo_uri}"
                        )
                        continue

                    # Use digest directly to fetch manifest
                    # This avoids issues with missing or changed tags
                    diff_ids = get_image_diff_ids_by_digest(
                        ecr_client, repo_name, digest
                    )
                    if diff_ids:
                        image_layers_data[uri] = diff_ids
                except Exception as e:
                    logger.debug(f"Could not get layers for {uri}: {e}")
                    continue

        if image_layers_data:
            layers = transform_ecr_image_layers(image_layers_data, image_digest_map)
            load_ecr_image_layers(
                neo4j_session,
                layers,
                region,
                current_aws_account_id,
                update_tag,
            )

    cleanup(neo4j_session, common_job_parameters)
