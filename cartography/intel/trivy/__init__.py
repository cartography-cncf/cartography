import json
import logging
from typing import Any

import boto3
from neo4j import Session

from cartography.client.aws import list_accounts
from cartography.client.aws.ecr import get_ecr_images
from cartography.client.gcp.artifact_registry import get_gcp_container_images
from cartography.client.gitlab.container_images import get_gitlab_container_images
from cartography.client.gitlab.container_images import get_gitlab_container_tags
from cartography.config import Config
from cartography.intel.trivy.scanner import cleanup
from cartography.intel.trivy.scanner import get_json_files_in_dir
from cartography.intel.trivy.scanner import get_json_files_in_s3
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
    source: str,
) -> tuple[dict[str, Any], str] | None:
    """
    Determine the tag URI that corresponds to this Trivy payload.

    Returns (trivy_data, display_uri) if the payload can be linked to an image present
    in the graph; otherwise returns None so the caller can skip ingestion.
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

    if not display_uri:
        logger.debug(
            "Skipping Trivy results for %s because no matching image URI was found in the graph",
            source,
        )
        return None

    return trivy_data, display_uri


@timeit
def sync_trivy_from_s3(
    neo4j_session: Session,
    trivy_s3_bucket: str,
    trivy_s3_prefix: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    boto3_session: boto3.Session,
) -> None:
    """
    Sync Trivy scan results from S3 for container images (ECR, GCP, and GitLab).

    Args:
        neo4j_session: Neo4j session for database operations
        trivy_s3_bucket: S3 bucket containing scan results
        trivy_s3_prefix: S3 prefix path containing scan results
        update_tag: Update tag for tracking
        common_job_parameters: Common job parameters for cleanup
        boto3_session: boto3 session for S3 operations
    """
    logger.info(
        f"Using Trivy scan results from s3://{trivy_s3_bucket}/{trivy_s3_prefix}"
    )

    image_uris, digest_aliases = _get_scan_targets_and_aliases(neo4j_session)
    json_files: set[str] = get_json_files_in_s3(
        trivy_s3_bucket, trivy_s3_prefix, boto3_session
    )

    if len(json_files) == 0:
        logger.error(
            f"Trivy sync was configured, but there are no json scan results in bucket "
            f"'{trivy_s3_bucket}' with prefix '{trivy_s3_prefix}'. "
            "Skipping Trivy sync to avoid potential data loss. "
            "Please check the S3 bucket and prefix configuration. We expect the json files in s3 to be named "
            f"`<image_uri>.json` and to be in the same bucket and prefix as the scan results. If the prefix is "
            "a folder, it MUST end with a trailing slash '/'. "
        )
        raise ValueError("No json scan results found in S3.")

    logger.info(f"Processing {len(json_files)} Trivy result files from S3")
    s3_client = boto3_session.client("s3")
    for s3_object_key in json_files:
        logger.debug(
            f"Reading scan results from S3: s3://{trivy_s3_bucket}/{s3_object_key}"
        )
        response = s3_client.get_object(Bucket=trivy_s3_bucket, Key=s3_object_key)
        scan_data_json = response["Body"].read().decode("utf-8")
        trivy_data = json.loads(scan_data_json)

        prepared = _prepare_trivy_data(
            trivy_data,
            image_uris=image_uris,
            digest_aliases=digest_aliases,
            source=f"s3://{trivy_s3_bucket}/{s3_object_key}",
        )
        if prepared is None:
            continue

        prepared_data, display_uri = prepared
        sync_single_image(
            neo4j_session,
            prepared_data,
            display_uri,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)


@timeit
def sync_trivy_from_dir(
    neo4j_session: Session,
    results_dir: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """Sync Trivy scan results from local files for container images (ECR, GCP, and GitLab)."""
    logger.info(f"Using Trivy scan results from {results_dir}")

    image_uris, digest_aliases = _get_scan_targets_and_aliases(neo4j_session)
    json_files: set[str] = get_json_files_in_dir(results_dir)

    if not json_files:
        logger.error(
            f"Trivy sync was configured, but no json files were found in {results_dir}."
        )
        raise ValueError("No Trivy json results found on disk")

    logger.info(f"Processing {len(json_files)} local Trivy result files")

    for file_path in json_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                trivy_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to read Trivy data from {file_path}: {e}")
            continue

        prepared = _prepare_trivy_data(
            trivy_data,
            image_uris=image_uris,
            digest_aliases=digest_aliases,
            source=file_path,
        )
        if prepared is None:
            continue

        prepared_data, display_uri = prepared
        sync_single_image(
            neo4j_session,
            prepared_data,
            display_uri,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)


@timeit
def start_trivy_ingestion(neo4j_session: Session, config: Config) -> None:
    """Start Trivy scan ingestion from S3 or local files.

    Args:
        neo4j_session: Neo4j session for database operations
        config: Configuration object containing S3 or directory paths
    """
    if not config.trivy_s3_bucket and not config.trivy_results_dir:
        logger.info("Trivy configuration not provided. Skipping Trivy ingestion.")
        return

    if config.trivy_results_dir:
        common_job_parameters = {
            "UPDATE_TAG": config.update_tag,
        }
        sync_trivy_from_dir(
            neo4j_session,
            config.trivy_results_dir,
            config.update_tag,
            common_job_parameters,
        )
        return

    if config.trivy_s3_prefix is None:
        config.trivy_s3_prefix = ""

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    boto3_session = boto3.Session()

    sync_trivy_from_s3(
        neo4j_session,
        config.trivy_s3_bucket,
        config.trivy_s3_prefix,
        config.update_tag,
        common_job_parameters,
        boto3_session,
    )

    # Support other Trivy resource types here e.g. if Google Cloud has images.
