import asyncio
import logging
from typing import Any
from typing import Dict
from typing import Optional

import aioboto3
import boto3
import httpx
import neo4j

from cartography.client.core.tx import load_graph_data
from cartography.client.core.tx import run_write_query
from cartography.intel.aws import ecr
from cartography.intel.aws.ecr_shared import batch_get_manifest
from cartography.intel.aws.ecr_shared import ECR_DOCKER_MANIFEST_MT
from cartography.intel.aws.ecr_shared import ECR_OCI_MANIFEST_MT
from cartography.intel.aws.ecr_shared import ECRFetchTransientError
from cartography.intel.aws.ecr_shared import get_blob_json_via_presigned
from cartography.intel.supply_chain import extract_workflow_path_from_ref
from cartography.intel.supply_chain import normalize_vcs_url
from cartography.util import timeit

logger = logging.getLogger(__name__)


ECR_IMAGE_PROVENANCE_QUERY = """
UNWIND $DictList AS item
MATCH (:AWSAccount {id: $AWS_ID})-[:RESOURCE]->(img:ECRImage)
WHERE img.region = $Region
  AND img.id = item["imageDigest"]
SET
    img.source_uri = item["source_uri"],
    img.source_revision = item["source_revision"],
    img.invocation_uri = item["invocation_uri"],
    img.invocation_workflow = item["invocation_workflow"],
    img.invocation_run_number = item["invocation_run_number"],
    img.source_file = item["source_file"],
    img.provenance_lastupdated = $update_tag
"""


ECR_IMAGE_BUILT_FROM_QUERY = """
UNWIND $DictList AS item
MATCH (:AWSAccount {id: $AWS_ID})-[:RESOURCE]->(child:ECRImage)
WHERE child.region = $Region
  AND child.id = item["imageDigest"]
MATCH (:AWSAccount {id: $AWS_ID})-[:RESOURCE]->(parent:ECRImage)
WHERE parent.region = $Region
  AND parent.id = item["parent_image_digest"]
MERGE (child)-[r:BUILT_FROM]->(parent)
ON CREATE SET r.firstseen = timestamp()
SET
    r.lastupdated = $update_tag,
    r.from_attestation = item["from_attestation"],
    r.parent_image_uri = item["parent_image_uri"],
    r.confidence = item["confidence"]
"""


STALE_ECR_IMAGE_PROVENANCE_QUERY = """
MATCH (:AWSAccount {id: $AWS_ID})-[:RESOURCE]->(img:ECRImage)
WHERE img.region = $Region
  AND img.provenance_lastupdated IS NOT NULL
  AND img.provenance_lastupdated <> $update_tag
SET
    img.source_uri = NULL,
    img.source_revision = NULL,
    img.invocation_uri = NULL,
    img.invocation_workflow = NULL,
    img.invocation_run_number = NULL,
    img.source_file = NULL,
    img.provenance_lastupdated = NULL
"""


STALE_BUILT_FROM_QUERY = """
MATCH (:AWSAccount {id: $AWS_ID})-[:RESOURCE]->(img:ECRImage)-[r:BUILT_FROM]->(:ECRImage)
WHERE img.region = $Region
  AND coalesce(r.from_attestation, false) = true
  AND r.lastupdated <> $update_tag
DELETE r
"""


def _collect_attestations(
    repo_data: Dict[str, Any],
) -> list[dict[str, str]]:
    """Extract attestation metadata from ECR image inventory."""
    attestations = []
    for repo_uri, images in repo_data.items():
        repo_name = repo_uri.split("/", 1)[1] if "/" in repo_uri else repo_uri
        for img in images:
            for manifest_img in img.get("_manifest_images", []):
                if manifest_img.get("type") == "attestation" and manifest_img.get(
                    "attests_digest"
                ):
                    attestations.append(
                        {
                            "repo_name": repo_name,
                            "digest": manifest_img["digest"],
                            "attests_digest": manifest_img["attests_digest"],
                        }
                    )
    return attestations


async def _extract_provenance_from_attestation(
    ecr_client: Any,
    repo_name: str,
    attestation_manifest_digest: str,
    http_client: httpx.AsyncClient,
) -> Optional[dict[str, Any]]:
    """Extract provenance from an in-toto SLSA attestation manifest."""
    attestation_manifest, _ = await batch_get_manifest(
        ecr_client,
        repo_name,
        attestation_manifest_digest,
        [ECR_OCI_MANIFEST_MT, ECR_DOCKER_MANIFEST_MT],
    )
    if not attestation_manifest:
        return None

    layers = attestation_manifest.get("layers", [])
    intoto_layer = next(
        (layer for layer in layers if "in-toto" in layer.get("mediaType", "").lower()),
        None,
    )
    if not intoto_layer:
        return None

    intoto_digest = intoto_layer.get("digest")
    if not intoto_digest:
        return None

    attestation_blob = await get_blob_json_via_presigned(
        ecr_client,
        repo_name,
        intoto_digest,
        http_client,
    )
    if not attestation_blob:
        return None

    predicate = attestation_blob.get("predicate", {})
    result: dict[str, Any] = {}

    dependency_list: list[dict[str, Any]] = predicate.get("materials", [])
    if not dependency_list:
        build_def = predicate.get("buildDefinition", {})
        dependency_list = build_def.get("resolvedDependencies", [])

    for dep in dependency_list:
        uri = dep.get("uri", "")
        uri_l = uri.lower()
        is_container_ref = (
            uri_l.startswith("pkg:docker/")
            or uri_l.startswith("pkg:oci/")
            or uri_l.startswith("oci://")
        )
        if is_container_ref and "dockerfile" not in uri_l:
            sha = dep.get("digest", {}).get("sha256")
            if sha:
                result["parent_image_uri"] = uri
                result["parent_image_digest"] = f"sha256:{sha}"
                break

    metadata = predicate.get("metadata", {})
    vcs = metadata.get("https://mobyproject.org/buildkit@v1#metadata", {}).get(
        "vcs", {}
    )
    if not vcs:
        rd = predicate.get("runDetails", {}).get("metadata", {})
        vcs = rd.get("buildkit_metadata", {}).get("vcs", {})

    if vcs.get("source"):
        result["source_uri"] = normalize_vcs_url(vcs["source"])
    if vcs.get("revision"):
        result["source_revision"] = vcs["revision"]

    invocation = predicate.get("invocation", {})
    env = invocation.get("environment", {})
    if env.get("github_repository"):
        server = env.get("github_server_url", "https://github.com").rstrip("/")
        result["invocation_uri"] = f"{server}/{env['github_repository']}"
    if env.get("github_workflow_ref"):
        workflow = extract_workflow_path_from_ref(env["github_workflow_ref"])
        if workflow:
            result["invocation_workflow"] = workflow
    if env.get("github_run_number"):
        result["invocation_run_number"] = env["github_run_number"]

    if "invocation_uri" not in result:
        builder_id = predicate.get("runDetails", {}).get("builder", {}).get("id", "")
        if "github.com" in builder_id and "/actions/runs/" in builder_id:
            parts = builder_id.split("/actions/runs/")
            if len(parts) == 2:
                result["invocation_uri"] = parts[0]

    if "source_uri" in result:
        entry_point = invocation.get("configSource", {}).get("entryPoint", "")
        if not entry_point:
            build_def = predicate.get("buildDefinition", {})
            entry_point = (
                build_def.get("externalParameters", {})
                .get("configSource", {})
                .get("path", "Dockerfile")
            )
        if not entry_point:
            entry_point = "Dockerfile"
        dockerfile_dir = (
            (vcs.get("localdir:dockerfile") or "").removeprefix("./").rstrip("/")
        )
        result["source_file"] = (
            f"{dockerfile_dir}/{entry_point}" if dockerfile_dir else entry_point
        )

    return result or None


async def _fetch_provenance_for_attestations(
    aioboto3_session: aioboto3.Session,
    region: str,
    attestations: list[dict[str, str]],
) -> dict[str, dict[str, Any]]:
    """Fetch provenance from attestation blobs concurrently."""
    provenance_map: dict[str, dict[str, Any]] = {}
    semaphore = asyncio.Semaphore(200)

    async with aioboto3_session.client("ecr", region_name=region) as ecr_client:
        async with httpx.AsyncClient() as http_client:

            async def _process(att: dict[str, str]) -> None:
                async with semaphore:
                    try:
                        provenance = await _extract_provenance_from_attestation(
                            ecr_client,
                            att["repo_name"],
                            att["digest"],
                            http_client,
                        )
                    except ECRFetchTransientError:
                        logger.warning(
                            "Skipping provenance for attestation %s after transient error.",
                            att["digest"],
                        )
                        return

                    if provenance:
                        provenance_map[att["attests_digest"]] = provenance

            tasks = [asyncio.create_task(_process(att)) for att in attestations]
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, ECRFetchTransientError):
                        continue
                    if isinstance(result, Exception):
                        logger.warning(
                            "Unexpected error extracting provenance: %s: %s",
                            type(result).__name__,
                            result,
                        )

    return provenance_map


def _fetch_provenance(
    aioboto3_session: aioboto3.Session,
    region: str,
    repo_data: Dict[str, Any],
) -> dict[str, dict[str, Any]]:
    attestations = _collect_attestations(repo_data)
    if not attestations:
        return {}

    logger.info("Fetching provenance from %d attestation images.", len(attestations))

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    provenance_map = loop.run_until_complete(
        _fetch_provenance_for_attestations(aioboto3_session, region, attestations)
    )
    logger.info("Extracted provenance for %d images.", len(provenance_map))
    return provenance_map


def transform_ecr_image_provenance(
    provenance_map: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    provenance_items = []
    for image_digest in sorted(provenance_map):
        provenance_items.append(
            {
                "imageDigest": image_digest,
                "from_attestation": True,
                "confidence": "explicit",
                **provenance_map[image_digest],
            }
        )
    return provenance_items


@timeit
def load_ecr_image_provenance(
    neo4j_session: neo4j.Session,
    provenance_items: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    if not provenance_items:
        return

    logger.info(
        "Loading provenance properties for %d ECR images in region %s.",
        len(provenance_items),
        region,
    )
    load_graph_data(
        neo4j_session,
        ECR_IMAGE_PROVENANCE_QUERY,
        provenance_items,
        AWS_ID=current_aws_account_id,
        Region=region,
        update_tag=update_tag,
    )


@timeit
def load_ecr_image_parent_relationships(
    neo4j_session: neo4j.Session,
    provenance_items: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    built_from_items = [
        item for item in provenance_items if item.get("parent_image_digest")
    ]
    if not built_from_items:
        return

    logger.info(
        "Loading BUILT_FROM relationships for %d ECR images in region %s.",
        len(built_from_items),
        region,
    )
    load_graph_data(
        neo4j_session,
        ECR_IMAGE_BUILT_FROM_QUERY,
        built_from_items,
        AWS_ID=current_aws_account_id,
        Region=region,
        update_tag=update_tag,
    )


def cleanup(
    neo4j_session: neo4j.Session,
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    run_write_query(
        neo4j_session,
        STALE_BUILT_FROM_QUERY,
        AWS_ID=current_aws_account_id,
        Region=region,
        update_tag=update_tag,
    )
    run_write_query(
        neo4j_session,
        STALE_ECR_IMAGE_PROVENANCE_QUERY,
        AWS_ID=current_aws_account_id,
        Region=region,
        update_tag=update_tag,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    aioboto3_session: aioboto3.Session | None = None,
) -> None:
    del common_job_parameters

    if aioboto3_session is None:
        raise ValueError("ecr:provenance requires an aioboto3_session")

    for region in regions:
        logger.info(
            "Syncing ECR provenance for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        repositories = ecr.get_ecr_repositories(boto3_session, region)
        image_data = ecr.get_repository_image_data(boto3_session, region, repositories)
        provenance_map = _fetch_provenance(aioboto3_session, region, image_data)
        provenance_items = transform_ecr_image_provenance(provenance_map)
        load_ecr_image_provenance(
            neo4j_session,
            provenance_items,
            region,
            current_aws_account_id,
            update_tag,
        )
        load_ecr_image_parent_relationships(
            neo4j_session,
            provenance_items,
            region,
            current_aws_account_id,
            update_tag,
        )
        cleanup(neo4j_session, region, current_aws_account_id, update_tag)
