import logging
from typing import Any

import boto3
from neo4j import Session

from cartography.client.aws import list_accounts
from cartography.client.aws.ecr import get_ecr_images
from cartography.config import Config
from cartography.intel.trivy.scanner import cleanup
from cartography.intel.trivy.scanner import list_s3_scan_results
from cartography.intel.trivy.scanner import sync_single_image_from_s3
from cartography.stats import get_stats_client
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client("trivy.scanner")


@timeit
def get_scan_targets(
    neo4j_session: Session,
    account_ids: list[str] | None = None,
) -> list[tuple[str, str, str, str, str]]:
    """
    Return list of ECR images from all accounts in the graph as tuples with shape (region, image_tag, image_uri,
    repo_name, image_digest).
    """
    if not account_ids:
        aws_accounts = list_accounts(neo4j_session)
    else:
        aws_accounts = account_ids

    ecr_images: list[tuple[str, str, str, str, str]] = []
    for account_id in aws_accounts:
        ecr_images.extend(get_ecr_images(neo4j_session, account_id))
    return ecr_images


@timeit
def sync_trivy_aws_ecr_from_s3(
    neo4j_session: Session,
    trivy_s3_bucket: str,
    trivy_s3_prefix: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    boto3_session: boto3.Session,
) -> None:
    """
    Sync Trivy scan results from S3 for AWS ECR images.

    Args:
        neo4j_session: Neo4j session for database operations
        ecr_images: List of ECR image tuples (region, image_tag, image_uri, repo_name, image_digest)
        trivy_s3_bucket: S3 bucket containing scan results
        trivy_s3_prefix: S3 prefix path containing scan results
        update_tag: Update tag for tracking
        common_job_parameters: Common job parameters for cleanup
        boto3_session: boto3 session for S3 operations
    """
    logger.info(
        f"Using S3 scanning from bucket {trivy_s3_bucket} with prefix {trivy_s3_prefix}"
    )

    # Get the list of ECR images from the graph
    ecr_images = get_scan_targets(neo4j_session)

    # Get list of ECR images that have corresponding S3 scan results
    s3_scan_results = list_s3_scan_results(
        trivy_s3_bucket,
        trivy_s3_prefix,
        ecr_images,
        boto3_session,
    )

    logger.info(f"Processing {len(s3_scan_results)} ECR images with S3 scan results")

    # Process images with S3 scan results
    for (
        _,
        _,
        image_uri,
        _,
        image_digest,
        s3_object_key,
    ) in s3_scan_results:
        sync_single_image_from_s3(
            neo4j_session,
            image_uri,
            image_digest,
            update_tag,
            trivy_s3_bucket,
            s3_object_key,
            boto3_session,
        )

    cleanup(neo4j_session, common_job_parameters)


@timeit
def start_trivy_ingestion(neo4j_session: Session, config: Config) -> None:
    """
    Start Trivy scan ingestion from S3.

    Args:
        neo4j_session: Neo4j session for database operations
        config: Configuration object containing S3 settings
    """
    # Check if S3 configuration is provided
    if not config.trivy_s3_bucket or not config.trivy_s3_prefix:
        logger.info("Trivy S3 configuration not provided. Skipping Trivy ingestion.")
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    # Get ECR images to scan
    boto3_session = boto3.Session()

    sync_trivy_aws_ecr_from_s3(
        neo4j_session,
        config.trivy_s3_bucket,
        config.trivy_s3_prefix,
        config.update_tag,
        common_job_parameters,
        boto3_session,
    )

    # Support other Trivy resource types here e.g. if Google Cloud has images.
