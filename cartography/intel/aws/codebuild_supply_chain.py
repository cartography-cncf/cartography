import logging
import re
from collections import defaultdict
from typing import Any

import boto3
import botocore.exceptions
import neo4j

from cartography.client.core.tx import load_matchlinks
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.client.core.tx import run_write_query
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

# ListBuildsForProject returns the newest builds first. Images that outlive this many
# builds of their project keep the edge from an earlier sync (see _cleanup_reevaluated).
MAX_BUILDS_PER_PROJECT = 50
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
def get_recent_builds(
    boto3_session: boto3.Session,
    region: str,
    project_names: list[str],
    max_builds_per_project: int = MAX_BUILDS_PER_PROJECT,
) -> list[dict[str, Any]] | None:
    """
    Return the region's recent builds, or None when the region could not be read.

    aws_handle_regions reports a skipped region as an empty list, which a region with
    no builds also returns, so the builds are wrapped to keep the two apart.
    """
    pages = _get_recent_builds(
        boto3_session, region, project_names, max_builds_per_project
    )
    if not pages:
        return None
    return pages[0]["builds"]


@aws_handle_regions
def _get_recent_builds(
    boto3_session: boto3.Session,
    region: str,
    project_names: list[str],
    max_builds_per_project: int,
) -> list[dict[str, Any]]:
    client = create_boto3_client(
        boto3_session, "codebuild", region_name=region, config=get_botocore_config()
    )
    build_ids: list[str] = []
    for project_name in project_names:
        try:
            response = client.list_builds_for_project(
                projectName=project_name,
                sortOrder="DESCENDING",
            )
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
        build_ids.extend(response.get("ids", [])[:max_builds_per_project])

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
        uuid_match = _UUID_RE.search(build_id.rsplit(":", 1)[-1].lower())
        revision = (build.get("resolvedSourceVersion") or "").strip().lower()
        transformed.append(
            {
                "build_id": build_id,
                "build_uuid": uuid_match.group(0) if uuid_match else None,
                "project_arn": _project_arn_from_build_arn(build_arn),
                "source_revision": revision if _SHA_RE.match(revision) else None,
                "source_uri": normalize_vcs_url(location),
                "source_provider": provider,
            }
        )
    return transformed


@timeit
def get_account_ecr_images(
    neo4j_session: neo4j.Session,
    account_id: str,
) -> list[dict[str, Any]]:
    """
    Return each ECR image in the account with its tags and, for a manifest list, the
    digests of the platform images it contains.
    """
    query = """
        MATCH (:AWSAccount {id: $AWS_ID})-[:RESOURCE]->(:AWSECRRepository)
              -[:REPO_IMAGE]->(repo_img:AWSECRRepositoryImage)-[:IMAGE]->(img:AWSECRImage)
        WHERE repo_img.tag IS NOT NULL
        WITH img, collect(DISTINCT repo_img.tag) AS tags
        OPTIONAL MATCH (img)-[:CONTAINS_IMAGE]->(child:AWSECRImage)
        RETURN img.digest AS digest, tags, collect(DISTINCT child.digest) AS child_digests
    """
    return neo4j_session.execute_read(read_list_of_dicts_tx, query, AWS_ID=account_id)


def _normalized_tags(image: dict[str, Any]) -> list[str]:
    return [tag.strip().lower() for tag in image.get("tags") or [] if tag]


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
) -> tuple[list[dict[str, Any]], set[str]]:
    """
    Tie images to the builds that pushed them.

    Returns the PACKAGED_BY rows and the digests the current builds carry evidence for,
    matched or not. Only those digests are eligible for stale-edge cleanup.

    match_revisions is off when some region's builds could not be read: a build ID is
    unique on its own, but a commit can look unambiguous only because the other
    projects that built it were not visible.
    """
    builds_by_uuid = _builds_by_uuid(builds)
    targets_by_revision = _targets_by_revision(builds)

    rows: list[dict[str, Any]] = []
    evidenced: set[str] = set()
    for image in images:
        tags = _normalized_tags(image)
        digests = [image["digest"], *(image.get("child_digests") or [])]

        has_build_id_evidence = any(
            uuid in builds_by_uuid for tag in tags for uuid in _UUID_RE.findall(tag)
        )
        has_revision_evidence = match_revisions and any(
            _SHA_RE.match(tag) and _revision_targets_for_tag(tag, targets_by_revision)
            for tag in tags
        )
        if not has_build_id_evidence and not has_revision_evidence:
            continue
        evidenced.update(digests)

        match = _match_build_id_tags(tags, builds_by_uuid)
        if match is None and not has_build_id_evidence:
            match = _match_revision_tags(tags, targets_by_revision)
        if match is None:
            continue
        rows.extend({"image_digest": digest, **match} for digest in digests)
    return rows, evidenced


def _cleanup_reevaluated(
    neo4j_session: neo4j.Session,
    digests: set[str],
    account_id: str,
    update_tag: int,
) -> None:
    """
    Remove this account's stale CodeBuild PACKAGED_BY edges, but only for images the
    current builds re-evaluated. An image whose build fell out of the recent-build window
    keeps its edge; deleting the image or the project removes it.
    """
    if not digests:
        return
    run_write_query(
        neo4j_session,
        """
        UNWIND $digests AS digest
        MATCH (:AWSECRImage {id: digest})-[r:PACKAGED_BY]->(:AWSCodeBuildProject)
        WHERE r._sub_resource_label = 'AWSAccount'
          AND r._sub_resource_id = $account_id
          AND r.lastupdated <> $update_tag
        DELETE r
        """,
        digests=list(digests),
        account_id=account_id,
        update_tag=update_tag,
    )


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
    """
    builds: list[dict[str, Any]] = []
    unreadable_regions: list[str] = []
    for region, projects in projects_by_region.items():
        project_names = projects_with_linkable_source(projects)
        if not project_names:
            continue
        region_builds = get_recent_builds(boto3_session, region, project_names)
        if region_builds is None:
            unreadable_regions.append(region)
            continue
        builds.extend(transform_builds(region_builds))
    if not builds:
        return
    if unreadable_regions:
        logger.warning(
            "CodeBuild builds could not be read in %s for account %s; matching images "
            "by build ID only.",
            ", ".join(unreadable_regions),
            current_aws_account_id,
        )

    images = get_account_ecr_images(neo4j_session, current_aws_account_id)
    rows, evidenced = match_images_to_builds(
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
    _cleanup_reevaluated(neo4j_session, evidenced, current_aws_account_id, update_tag)
