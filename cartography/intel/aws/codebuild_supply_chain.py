import logging
import re
from collections import defaultdict
from typing import Any

import boto3
import botocore.exceptions
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

# A build ID embeds a random UUID, so a tag carrying it identifies one build. A commit SHA
# tag only identifies a revision that several projects may build, hence the lower score,
# matching the CircleCI tag-revision rung.
CODEBUILD_BUILD_ID_TAG_CONFIDENCE = 0.9
CODEBUILD_TAG_REVISION_CONFIDENCE = 0.5

# ListBuildsForProject returns the newest builds first. Build IDs are cheap to list, so a
# long history is scanned for the build IDs found in image tags; only the most recent
# builds are fetched in full to resolve commit SHA tags.
MAX_LISTED_BUILDS_PER_PROJECT = 1000
MAX_RECENT_BUILDS_PER_PROJECT = 50
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


def projects_with_linkable_source(projects: list[dict[str, Any]]) -> list[str]:
    return [
        project["name"]
        for project in projects
        if project.get("source", {}).get("type") in SOURCE_PROVIDERS
        and project.get("name")
    ]


@timeit
def get_builds(
    boto3_session: boto3.Session,
    region: str,
    project_names: list[str],
    tagged_build_uuids: set[str],
) -> list[dict[str, Any]] | None:
    """
    Return each project's recent builds plus any older build named by an image tag, or
    None when the region could not be read.

    aws_handle_regions reports a skipped region as an empty list, which a region with
    no builds also returns, so the builds are wrapped to keep the two apart.
    """
    pages = _get_builds(boto3_session, region, project_names, tagged_build_uuids)
    if not pages:
        return None
    return pages[0]["builds"]


def _build_uuid(build_id: str) -> str | None:
    uuid_match = _UUID_RE.search(build_id.rsplit(":", 1)[-1].lower())
    return uuid_match.group(0) if uuid_match else None


def select_build_ids(
    listed_build_ids: list[str],
    tagged_build_uuids: set[str],
) -> list[str]:
    recent = listed_build_ids[:MAX_RECENT_BUILDS_PER_PROJECT]
    tagged = [
        build_id
        for build_id in listed_build_ids[MAX_RECENT_BUILDS_PER_PROJECT:]
        if _build_uuid(build_id) in tagged_build_uuids
    ]
    return recent + tagged


@aws_handle_regions
def _get_builds(
    boto3_session: boto3.Session,
    region: str,
    project_names: list[str],
    tagged_build_uuids: set[str],
) -> list[dict[str, Any]]:
    client = create_boto3_client(
        boto3_session, "codebuild", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("list_builds_for_project")
    build_ids: list[str] = []
    for project_name in project_names:
        listed: list[str] = []
        try:
            for page in paginator.paginate(
                projectName=project_name,
                sortOrder="DESCENDING",
                PaginationConfig={"MaxItems": MAX_LISTED_BUILDS_PER_PROJECT},
            ):
                listed.extend(page.get("ids", []))
        except botocore.exceptions.ClientError as error:
            if (
                error.response.get("Error", {}).get("Code")
                == "ResourceNotFoundException"
            ):
                logger.debug(
                    "CodeBuild project %s disappeared before its builds were listed.",
                    project_name,
                )
                continue
            raise
        build_ids.extend(select_build_ids(listed, tagged_build_uuids))

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
        source = build.get("source") or {}
        provider = SOURCE_PROVIDERS.get(source.get("type", ""))
        location = source.get("location")
        if not provider or not location:
            continue
        build_id = build["id"]
        build_arn = build["arn"]
        revision = (build.get("resolvedSourceVersion") or "").strip().lower()
        transformed.append(
            {
                "build_id": build_id,
                "build_uuid": _build_uuid(build_id),
                "project_arn": _project_arn_from_build_arn(build_arn),
                "source_revision": revision if _SHA_RE.match(revision) else None,
                "source_uri": normalize_vcs_url(location),
                "source_provider": provider,
            }
        )
    return transformed


def group_tags_by_digest(
    ecr_images: set[tuple[str, str, str, str, str]],
) -> list[dict[str, Any]]:
    """Group the (region, tag, uri, repo_name, digest) rows of get_ecr_images."""
    tags_by_digest: dict[str, set[str]] = defaultdict(set)
    for _region, tag, _uri, _repo_name, digest in ecr_images:
        if tag:
            tags_by_digest[digest].add(tag.strip().lower())
    return [
        {"digest": digest, "tags": sorted(tags)}
        for digest, tags in sorted(tags_by_digest.items())
    ]


def tagged_build_uuids(images: list[dict[str, Any]]) -> set[str]:
    return {
        uuid
        for image in images
        for tag in image["tags"]
        for uuid in _UUID_RE.findall(tag)
    }


def _builds_by_uuid(builds: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {build["build_uuid"]: build for build in builds if build["build_uuid"]}


def _targets_by_revision(
    builds: list[dict[str, Any]],
) -> dict[str, set[tuple[str, str, str]]]:
    targets: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    for build in builds:
        if build["source_revision"]:
            targets[build["source_revision"]].add(
                (build["project_arn"], build["source_uri"], build["source_provider"])
            )
    return dict(targets)


def _revision_targets_for_tag(
    tag: str,
    targets_by_revision: dict[str, set[tuple[str, str, str]]],
) -> set[tuple[str, str, str]]:
    targets: set[tuple[str, str, str]] = set()
    for revision, revision_targets in targets_by_revision.items():
        if revision == tag or (len(tag) < len(revision) and revision.startswith(tag)):
            targets |= revision_targets
    return targets


def _match_build_id_tags(
    tags: list[str],
    builds_by_uuid: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    matched = {
        builds_by_uuid[uuid]["build_id"]: builds_by_uuid[uuid]
        for tag in tags
        for uuid in _UUID_RE.findall(tag)
        if uuid in builds_by_uuid
    }
    if len(matched) != 1:
        return None
    build = next(iter(matched.values()))
    return {
        "project_arn": build["project_arn"],
        "build_id": build["build_id"],
        "source_revision": build["source_revision"],
        "source_uri": build["source_uri"],
        "source_provider": build["source_provider"],
        "match_method": "codebuild_build_id_tag",
        "confidence": CODEBUILD_BUILD_ID_TAG_CONFIDENCE,
    }


def _match_revision_tags(
    tags: list[str],
    targets_by_revision: dict[str, set[tuple[str, str, str]]],
) -> dict[str, Any] | None:
    """
    Every SHA-like tag is resolved and the targets unioned, so the image matches only
    when all of them agree on one project and repository.
    """
    targets: set[tuple[str, str, str]] = set()
    revisions: set[str] = set()
    for tag in tags:
        if not _SHA_RE.match(tag):
            continue
        tag_targets = _revision_targets_for_tag(tag, targets_by_revision)
        if tag_targets:
            targets |= tag_targets
            revisions |= {
                revision
                for revision in targets_by_revision
                if revision == tag or revision.startswith(tag)
            }
    if len(targets) != 1 or len(revisions) != 1:
        return None
    project_arn, source_uri, source_provider = next(iter(targets))
    return {
        "project_arn": project_arn,
        "build_id": None,
        "source_revision": next(iter(revisions)),
        "source_uri": source_uri,
        "source_provider": source_provider,
        "match_method": "codebuild_tag_revision",
        "confidence": CODEBUILD_TAG_REVISION_CONFIDENCE,
    }


def match_images_to_builds(
    images: list[dict[str, Any]],
    builds: list[dict[str, Any]],
    match_revisions: bool = True,
) -> list[dict[str, Any]]:
    """
    Tie images to the builds that pushed them and return the PACKAGED_BY rows.

    match_revisions is off when some region's builds could not be read: a build ID is
    unique on its own, but a commit can look unambiguous only because the other
    projects that built it were not visible.
    """
    builds_by_uuid = _builds_by_uuid(builds)
    targets_by_revision = _targets_by_revision(builds)

    rows: list[dict[str, Any]] = []
    for image in images:
        tags = image["tags"]
        has_build_id_evidence = any(
            uuid in builds_by_uuid for tag in tags for uuid in _UUID_RE.findall(tag)
        )
        if has_build_id_evidence:
            match = _match_build_id_tags(tags, builds_by_uuid)
        elif match_revisions:
            match = _match_revision_tags(tags, targets_by_revision)
        else:
            match = None
        if match is not None:
            rows.append({"image_digest": image["digest"], **match})
    return rows


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.Session,
    projects_by_region: dict[str, list[dict[str, Any]]],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Link ECR images to the CodeBuild projects that pushed them.

    Builds are read transiently and never stored as nodes. Matching runs once across all
    regions because a build can push to a registry in another region. The ontology stage
    then derives (:Image)-[:PACKAGED_FROM]->(repository) from these edges.

    Stale edges are cleaned up only when every region was read, so a permission or
    regional outage never deletes edges it cannot re-derive.
    """
    images = group_tags_by_digest(get_ecr_images(neo4j_session, current_aws_account_id))
    build_uuids = tagged_build_uuids(images)

    builds: list[dict[str, Any]] = []
    unreadable_regions: list[str] = []
    for region, projects in projects_by_region.items():
        project_names = projects_with_linkable_source(projects)
        if not project_names:
            continue
        region_builds = get_builds(boto3_session, region, project_names, build_uuids)
        if region_builds is None:
            unreadable_regions.append(region)
            continue
        builds.extend(transform_builds(region_builds))
    if unreadable_regions:
        logger.warning(
            "CodeBuild builds could not be read in %s for account %s; matching images "
            "by build ID only and keeping existing edges.",
            ", ".join(unreadable_regions),
            current_aws_account_id,
        )

    rows = match_images_to_builds(
        images, builds, match_revisions=not unreadable_regions
    )
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
    if not unreadable_regions:
        GraphJob.from_matchlink(
            ECRImagePackagedByCodeBuildProjectMatchLink(),
            "AWSAccount",
            current_aws_account_id,
            update_tag,
        ).run(neo4j_session)
