import logging
import re
from collections import defaultdict
from typing import Any

import boto3
import neo4j

from cartography.client.aws.ecr import get_ecr_images
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.intel.supply_chain import normalize_vcs_url
from cartography.models.aws.codebuild.image_matchlink import (
    ECRImagePackagedByCodeBuildProjectMatchLink,
)
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)

# A build ID embeds a random UUID, so a tag carrying it identifies one build.
CODEBUILD_BUILD_ID_TAG_CONFIDENCE = 0.9
_BATCH_GET_BUILDS_LIMIT = 100

# Source types whose location names a repository we can link to.
SOURCE_PROVIDERS = {
    "GITHUB": "github",
    "GITHUB_ENTERPRISE": "github",
    "GITLAB": "gitlab",
    "GITLAB_SELF_MANAGED": "gitlab",
}

_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


def linkable_source(source: dict[str, Any]) -> tuple[str, str] | None:
    """Return (provider, normalized repository URL) for a GitHub or GitLab source."""
    provider = SOURCE_PROVIDERS.get(source.get("type", ""))
    location = source.get("location")
    if not provider or not location:
        return None
    return provider, normalize_vcs_url(location)


def candidate_build_ids(
    ecr_images: set[tuple[str, str, str, str, str]],
    project_names: set[str],
) -> dict[str, set[str]]:
    """
    Map candidate build ID -> image digests, from build-ID image tags.

    A tag carries only the UUID of CODEBUILD_BUILD_ID (`<project>:<uuid>`). The project
    is taken to share the ECR repository's name, which BatchGetBuilds then confirms.
    """
    candidates: dict[str, set[str]] = defaultdict(set)
    for _region, tag, _uri, repo_name, digest in ecr_images:
        if not tag or repo_name not in project_names:
            continue
        for uuid in _UUID_RE.findall(tag.lower()):
            candidates[f"{repo_name}:{uuid}"].add(digest)
    return candidates


def build_ids_by_region(
    build_ids: set[str],
    project_names_by_region: dict[str, set[str]],
) -> dict[str, list[str]]:
    """Route each candidate build ID to every region holding a project of its name."""
    routed: dict[str, list[str]] = {}
    for region, project_names in sorted(project_names_by_region.items()):
        region_build_ids = sorted(
            build_id
            for build_id in build_ids
            if build_id.split(":", 1)[0] in project_names
        )
        if region_build_ids:
            routed[region] = region_build_ids
    return routed


@timeit
def get_builds(
    boto3_session: boto3.Session,
    region: str,
    build_ids: list[str],
) -> list[dict[str, Any]] | None:
    """
    Return the builds found for the given IDs, or None when the region could not be read.

    aws_handle_regions reports a skipped region as an empty list, which a region with
    no matching builds also returns, so the builds are wrapped to keep the two apart.
    """
    pages = _get_builds(boto3_session, region, build_ids)
    if not pages:
        return None
    return pages[0]["builds"]


@aws_handle_regions
def _get_builds(
    boto3_session: boto3.Session,
    region: str,
    build_ids: list[str],
) -> list[dict[str, Any]]:
    client = create_boto3_client(
        boto3_session, "codebuild", region_name=region, config=get_botocore_config()
    )
    builds: list[dict[str, Any]] = []
    for i in range(0, len(build_ids), _BATCH_GET_BUILDS_LIMIT):
        response = client.batch_get_builds(
            ids=build_ids[i : i + _BATCH_GET_BUILDS_LIMIT]
        )
        builds.extend(response.get("builds", []))
    return [{"builds": builds}]


def _project_arn_from_build_arn(build_arn: str) -> str:
    # arn:aws:codebuild:<region>:<account>:build/<project>:<uuid>
    return build_arn.rsplit(":", 1)[0].replace(":build/", ":project/", 1)


def transform_builds(builds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transformed = []
    for build in builds:
        source = linkable_source(build.get("source") or {})
        if source is None:
            continue
        provider, source_uri = source
        revision = (build.get("resolvedSourceVersion") or "").strip().lower()
        transformed.append(
            {
                "build_id": build["id"],
                "project_arn": _project_arn_from_build_arn(build["arn"]),
                "source_revision": revision if _SHA_RE.match(revision) else None,
                "source_uri": source_uri,
                "source_provider": provider,
            }
        )
    return transformed


def match_images_to_builds(
    candidates: dict[str, set[str]],
    builds: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return PACKAGED_BY rows for images whose tags name exactly one confirmed build."""
    builds_by_digest: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for build in builds:
        for digest in candidates.get(build["build_id"], ()):
            builds_by_digest[digest].append(build)

    rows = []
    for digest, digest_builds in sorted(builds_by_digest.items()):
        if len(digest_builds) != 1:
            continue
        rows.append(
            {
                "image_digest": digest,
                **digest_builds[0],
                "match_method": "codebuild_build_id_tag",
                "confidence": CODEBUILD_BUILD_ID_TAG_CONFIDENCE,
            }
        )
    return rows


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.Session,
    project_names_by_region: dict[str, set[str]],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Link ECR images tagged with a CodeBuild build ID to the project that built them.

    Builds are looked up in every region holding the same-named project, since a build
    can push to a registry in another region. They are read transiently and never
    stored as nodes. The ontology stage derives (:Image)-[:PACKAGED_FROM]->(repository)
    from these edges. Stale edges are cleaned up only when every lookup succeeded, so a
    permission or regional outage never deletes edges it cannot re-derive.
    """
    candidates = candidate_build_ids(
        get_ecr_images(neo4j_session, current_aws_account_id),
        set().union(*project_names_by_region.values()),
    )

    builds: list[dict[str, Any]] = []
    unreadable_regions: list[str] = []
    for region, build_ids in build_ids_by_region(
        set(candidates), project_names_by_region
    ).items():
        region_builds = get_builds(boto3_session, region, build_ids)
        if region_builds is None:
            unreadable_regions.append(region)
            continue
        builds.extend(transform_builds(region_builds))
    rows = match_images_to_builds(candidates, builds)

    logger.info(
        "Matched %d ECR image(s) to CodeBuild builds in account %s.",
        len(rows),
        current_aws_account_id,
    )
    if rows:
        load_matchlinks(
            neo4j_session,
            ECRImagePackagedByCodeBuildProjectMatchLink(),
            rows,
            lastupdated=update_tag,
            _sub_resource_label="AWSAccount",
            _sub_resource_id=current_aws_account_id,
        )
    if unreadable_regions:
        logger.warning(
            "CodeBuild builds could not be read in %s for account %s; keeping existing "
            "CodeBuild image edges.",
            ", ".join(unreadable_regions),
            current_aws_account_id,
        )
        return
    GraphJob.from_matchlink(
        ECRImagePackagedByCodeBuildProjectMatchLink(),
        "AWSAccount",
        current_aws_account_id,
        update_tag,
    ).run(neo4j_session)
