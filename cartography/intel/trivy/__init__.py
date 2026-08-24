import logging
import re
from typing import Any
from urllib.parse import urlparse

import boto3
from neo4j import Session

from cartography.client.aws import list_accounts
from cartography.client.aws.ecr import get_ecr_images
from cartography.client.gcp.artifact_registry import get_gcp_container_images
from cartography.client.gitlab.container_images import get_gitlab_container_images
from cartography.client.gitlab.container_images import get_gitlab_container_tags
from cartography.config import Config
from cartography.intel.common.object_store import filter_report_refs
from cartography.intel.common.object_store import LocalReportReader
from cartography.intel.common.object_store import ObjectStoreError
from cartography.intel.common.object_store import read_json_report
from cartography.intel.common.object_store import ReportReader
from cartography.intel.common.object_store import S3BucketReader
from cartography.intel.common.report_reader_builder import (
    build_report_reader_for_source,
)
from cartography.intel.common.report_source import parse_report_source
from cartography.intel.trivy.scanner import cleanup
from cartography.intel.trivy.scanner import cleanup_filesystem_snapshot_relationships
from cartography.intel.trivy.scanner import cleanup_image_relationships
from cartography.intel.trivy.scanner import sync_single_filesystem_snapshot
from cartography.intel.trivy.scanner import sync_single_image
from cartography.stats import get_stats_client
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client("trivy.scanner")


def _get_ecr_scan_targets_and_aliases(
    neo4j_session: Session,
    account_ids: list[str] | None = None,
) -> tuple[set[str], dict[str, str]]:
    """
    Return ECR tag URIs and a mapping of digest-qualified URIs to tag URIs.
    """
    if not account_ids:
        aws_accounts = list_accounts(neo4j_session)
    else:
        aws_accounts = account_ids

    image_uris: set[str] = set()
    digest_aliases: dict[str, str] = {}

    for account_id in aws_accounts:
        for _, _, image_uri, _, digest in get_ecr_images(neo4j_session, account_id):
            if not image_uri:
                continue
            image_uris.add(image_uri)
            if digest:
                # repo URI is everything before the trailing ":" (if present)
                repo_uri = image_uri.rsplit(":", 1)[0]
                digest_uri = f"{repo_uri}@{digest}"
                digest_aliases[digest_uri] = image_uri

    return image_uris, digest_aliases


def _get_gcp_scan_targets_and_aliases(
    neo4j_session: Session,
) -> tuple[set[str], dict[str, str]]:
    """
    Return GCP Artifact Registry container image URIs and a mapping of digest-qualified URIs to tag URIs.
    Matches ECR's pattern for consistency.
    """
    image_uris: set[str] = set()
    digest_aliases: dict[str, str] = {}

    for _, _, image_uri, _, digest in get_gcp_container_images(neo4j_session):
        if not image_uri:
            continue
        image_uris.add(image_uri)
        if digest:
            # repo URI is everything before the trailing ":" (if present)
            repo_uri = image_uri.rsplit(":", 1)[0]
            digest_uri = f"{repo_uri}@{digest}"
            digest_aliases[digest_uri] = image_uri

    return image_uris, digest_aliases


def _get_gitlab_scan_targets_and_aliases(
    neo4j_session: Session,
) -> tuple[set[str], dict[str, str]]:
    """
    Return GitLab container image URIs and a mapping of digest-qualified URIs to URIs.

    Includes both base URIs (from GitLabContainerImage nodes) and tagged URIs
    (from GitLabContainerRepositoryTag nodes) to support matching against both
    RepoTags and RepoDigests in Trivy scan results.
    """
    image_uris: set[str] = set()
    digest_aliases: dict[str, str] = {}

    # Get base URIs from container images
    for uri, digest in get_gitlab_container_images(neo4j_session):
        if not uri:
            continue
        image_uris.add(uri)
        if digest:
            # Map digest-qualified URI to base URI
            # e.g., registry.gitlab.com/group/project@sha256:abc -> registry.gitlab.com/group/project
            digest_uri = f"{uri}@{digest}"
            digest_aliases[digest_uri] = uri

    # Get tagged URIs from container repository tags
    # This enables matching against RepoTags in Trivy output (e.g., locally built images)
    for tag_location, digest in get_gitlab_container_tags(neo4j_session):
        if not tag_location:
            continue

        # Add the tagged URI to image_uris for direct matching
        # e.g., registry.gitlab.com/group/project:v1.0.0
        image_uris.add(tag_location)

        if digest:
            # Also create digest alias mapping for this tag
            # Strip the tag to get the repository URI
            repo_uri = (
                tag_location.rsplit(":", 1)[0] if ":" in tag_location else tag_location
            )
            digest_uri = f"{repo_uri}@{digest}"
            # Prefer tagged URI over base URI for display purposes
            # Don't overwrite if already exists (first tag wins)
            if digest_uri not in digest_aliases:
                digest_aliases[digest_uri] = tag_location

    return image_uris, digest_aliases


def _get_scan_targets_and_aliases(
    neo4j_session: Session,
    account_ids: list[str] | None = None,
) -> tuple[set[str], dict[str, str]]:
    """
    Return image URIs and digest aliases for ECR, GCP, and GitLab container images.
    """
    # Get ECR targets
    ecr_uris, ecr_aliases = _get_ecr_scan_targets_and_aliases(
        neo4j_session, account_ids
    )

    # Get GCP targets
    gcp_uris, gcp_aliases = _get_gcp_scan_targets_and_aliases(neo4j_session)

    # Get GitLab targets
    gitlab_uris, gitlab_aliases = _get_gitlab_scan_targets_and_aliases(neo4j_session)

    # Merge results
    image_uris = ecr_uris | gcp_uris | gitlab_uris
    digest_aliases = {**ecr_aliases, **gcp_aliases, **gitlab_aliases}

    return image_uris, digest_aliases


def _normalize_repository(value: str) -> str:
    repository = value.strip().rstrip("/")
    if repository.endswith(".git"):
        repository = repository[:-4]

    if "://" in repository:
        repository = urlparse(repository).path
    elif repository.startswith("git@") and ":" in repository:
        repository = repository.split(":", 1)[1]

    return repository.strip("/").lower()


def _get_filesystem_scan_targets(
    neo4j_session: Session,
) -> dict[tuple[str, str, str | None], list[str]]:
    """Return source repository, revision, and root mapped to snapshot IDs."""
    result = neo4j_session.run(
        """
        MATCH (snapshot:FilesystemSnapshot)
        WHERE snapshot.source_repo IS NOT NULL
          AND snapshot.source_revision IS NOT NULL
        RETURN snapshot.id AS id,
               snapshot.source_repo AS repository,
               snapshot.source_revision AS revision,
               snapshot.root_directory AS root_directory
        """,
    )
    targets: dict[tuple[str, str, str | None], list[str]] = {}
    for record in result:
        repository = _normalize_repository(record["repository"])
        revision = record["revision"].lower()
        root_directory = (record["root_directory"] or "").strip("/") or None
        targets.setdefault((repository, revision, root_directory), []).append(
            record["id"]
        )
    return targets


@timeit
def get_scan_targets(
    neo4j_session: Session,
    account_ids: list[str] | None = None,
) -> set[str]:
    """
    Return list of ECR images from all accounts in the graph.
    """
    image_uris, _ = _get_scan_targets_and_aliases(neo4j_session, account_ids)
    return image_uris


def _prepare_trivy_data(
    trivy_data: dict[str, Any],
    image_uris: set[str],
    digest_aliases: dict[str, str],
    filesystem_targets: dict[tuple[str, str, str | None], list[str]],
    source: str,
) -> tuple[dict[str, Any], str | None, list[str]] | None:
    """
    Determine the tag URI that corresponds to this Trivy payload.

    Returns the report and its matching image or filesystem snapshot targets.
    """

    artifact_name = (trivy_data.get("ArtifactName") or "").strip()
    metadata = trivy_data.get("Metadata") or {}
    candidates: list[str] = []

    if artifact_name:
        candidates.append(artifact_name)

    repo_tags = metadata.get("RepoTags", [])
    repo_digests = metadata.get("RepoDigests", [])
    stripped_tags_digests = [item.strip() for item in repo_tags + repo_digests]
    candidates.extend(stripped_tags_digests)

    display_uri: str | None = None

    for candidate in candidates:
        if not candidate:
            continue
        if candidate in image_uris:
            display_uri = candidate
            break
        alias = digest_aliases.get(candidate)
        if alias:
            display_uri = alias
            break

    if display_uri:
        return trivy_data, display_uri, []

    artifact_type = trivy_data.get("ArtifactType")
    repo_url = metadata.get("RepoURL")
    revision = metadata.get("Commit")
    root_directory = metadata.get("RootDirectory")
    if (
        artifact_type in {"filesystem", "repository"}
        and isinstance(repo_url, str)
        and isinstance(revision, str)
        and re.fullmatch(r"[0-9a-fA-F]{40}", revision)
    ):
        repository_key = _normalize_repository(repo_url)
        revision_key = revision.lower()
        if isinstance(root_directory, str):
            root_key = root_directory.strip("/") or None
            snapshot_ids = filesystem_targets.get(
                (repository_key, revision_key, root_key),
                [],
            )
        else:
            # Reports without a root predate this discriminator and represent
            # the whole repository, so retain the existing broad match.
            snapshot_ids = [
                snapshot_id
                for (repository, commit, _), ids in filesystem_targets.items()
                if repository == repository_key and commit == revision_key
                for snapshot_id in ids
            ]
        if snapshot_ids:
            return trivy_data, None, snapshot_ids

    logger.debug(
        "Skipping Trivy results for %s because no matching scan target was found in the graph",
        source,
    )
    return None


@timeit
def sync_trivy_from_report_reader(
    neo4j_session: Session,
    reader: ReportReader,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Trivy scan results from a cloud object store for container images (ECR, GCP, and GitLab).

    Args:
        neo4j_session: Neo4j session for database operations
        reader: Reader for listing and fetching reports
        update_tag: Update tag for tracking
        common_job_parameters: Common job parameters for cleanup
    """
    logger.info("Using Trivy scan results from %s", reader.source_uri)

    image_uris, digest_aliases = _get_scan_targets_and_aliases(neo4j_session)
    filesystem_targets = _get_filesystem_scan_targets(neo4j_session)
    json_files = filter_report_refs(
        reader.list_reports(),
        suffix=".json",
    )

    if len(json_files) == 0:
        logger.error(
            f"Trivy sync was configured, but there are no json scan results in {reader.source_uri}. "
            "Skipping Trivy sync to avoid potential data loss. "
            "Please check the configured source. We expect the json files to be named "
            "`<image_uri>.json` and to be in the configured report source. If the source is "
            "a folder, it MUST end with a trailing slash '/'. "
        )
        raise ValueError("No json scan results found in report source.")

    logger.info("Processing %d Trivy result files from report source", len(json_files))
    failed_report_count = 0
    processed_reports = 0
    processed_filesystem_reports = 0
    processed_image_reports = 0
    for ref in json_files:
        logger.debug(
            "Reading scan results from report source: %s",
            ref.uri,
        )
        try:
            trivy_data = read_json_report(reader, ref)
        except ObjectStoreError as exc:
            logger.error("Failed to read Trivy data from %s: %s", ref.uri, exc)
            failed_report_count += 1
            continue

        prepared = _prepare_trivy_data(
            trivy_data,
            image_uris=image_uris,
            digest_aliases=digest_aliases,
            filesystem_targets=filesystem_targets,
            source=ref.uri,
        )
        if prepared is None:
            continue

        prepared_data, display_uri, filesystem_snapshot_ids = prepared
        if display_uri:
            sync_single_image(
                neo4j_session,
                prepared_data,
                display_uri,
                update_tag,
            )
            processed_image_reports += 1
        else:
            sync_single_filesystem_snapshot(
                neo4j_session,
                prepared_data,
                filesystem_snapshot_ids,
                ref.uri,
                update_tag,
            )
            processed_filesystem_reports += 1
        processed_reports += 1

    if failed_report_count:
        logger.warning(
            "Skipping Trivy cleanup because %d report(s) failed to read or parse.",
            failed_report_count,
        )
        return

    if processed_reports == 0:
        logger.warning(
            "Skipping Trivy cleanup because no reports were ingested.",
        )
        return

    if image_uris and processed_image_reports == 0:
        logger.warning(
            "Limiting Trivy cleanup to filesystem relationships because the report "
            "source contained only filesystem reports while image scan targets exist.",
        )
        cleanup_filesystem_snapshot_relationships(neo4j_session, update_tag)
        return

    if filesystem_targets and processed_filesystem_reports == 0:
        logger.warning(
            "Limiting Trivy cleanup to image relationships because the report source "
            "contained only image reports while filesystem scan targets exist.",
        )
        cleanup_image_relationships(neo4j_session, update_tag)
        return

    cleanup(neo4j_session, common_job_parameters)


@timeit
def sync_trivy_from_s3(
    neo4j_session: Session,
    trivy_s3_bucket: str,
    trivy_s3_prefix: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    boto3_session: boto3.Session,
) -> None:
    # DEPRECATED: sync_trivy_from_s3() will be removed in v1.0.0.
    with S3BucketReader(
        boto3_session,
        trivy_s3_bucket,
        trivy_s3_prefix,
    ) as reader:
        sync_trivy_from_report_reader(
            neo4j_session,
            reader=reader,
            update_tag=update_tag,
            common_job_parameters=common_job_parameters,
        )


@timeit
def sync_trivy_from_dir(
    neo4j_session: Session,
    results_dir: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """Sync Trivy scan results from local files for container images (ECR, GCP, and GitLab)."""
    # DEPRECATED: sync_trivy_from_dir() will be removed in v1.0.0.
    sync_trivy_from_report_reader(
        neo4j_session,
        LocalReportReader(results_dir),
        update_tag,
        common_job_parameters,
    )


@timeit
def start_trivy_ingestion(neo4j_session: Session, config: Config) -> None:
    """Start Trivy scan ingestion from cloud object stores or local files.

    Args:
        neo4j_session: Neo4j session for database operations
        config: Configuration object containing S3 or directory paths
    """
    if not config.trivy_source:
        logger.info("Trivy configuration not provided. Skipping Trivy ingestion.")
        return

    source = parse_report_source(config.trivy_source)
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    with build_report_reader_for_source(
        source,
        config=config,
    ) as reader:
        sync_trivy_from_report_reader(
            neo4j_session,
            reader=reader,
            update_tag=config.update_tag,
            common_job_parameters=common_job_parameters,
        )

    # Support other Trivy resource types here e.g. if Google Cloud has images.
