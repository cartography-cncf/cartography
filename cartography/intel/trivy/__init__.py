import logging
import subprocess
from typing import Any

import boto3
from neo4j import Session

from cartography.client.aws import list_accounts
from cartography.client.aws.ecr import get_ecr_images
from cartography.config import Config
from cartography.intel.trivy.scanner import _call_trivy_update_db
from cartography.intel.trivy.scanner import cleanup
from cartography.intel.trivy.scanner import list_s3_scan_results
from cartography.intel.trivy.scanner import sync_single_image
from cartography.intel.trivy.scanner import sync_single_image_from_s3
from cartography.stats import get_stats_client
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client("trivy.scanner")


# If we have >= this percentage of Trivy fatal failures, crash the sync. 10 == 10%, 20 == 20%, etc.
# The circuit breaker exists so that if there is a high failure rate, we don't erroneously delete results from previous
# scans.
TRIVY_SCAN_FATAL_CIRCUIT_BREAKER_PERCENT = 10


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
    ecr_images: list[tuple[str, str, str, str, str]],
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
        region,
        image_tag,
        image_uri,
        repo_name,
        image_digest,
        s3_object_key,
    ) in s3_scan_results:
        sync_single_image_from_s3(
            neo4j_session,
            image_tag,
            image_uri,
            repo_name,
            image_digest,
            update_tag,
            trivy_s3_bucket,
            s3_object_key,
            boto3_session,
        )

    cleanup(neo4j_session, common_job_parameters)


@timeit
def sync_trivy_aws_ecr(
    neo4j_session: Session,
    trivy_path: str,
    trivy_opa_policy_file_path: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Trivy scan results for AWS ECR images using binary scanning.
    """
    ecr_images = get_scan_targets(neo4j_session)
    num_images = len(ecr_images)

    logger.info(f"Using binary scanning with Trivy for {num_images} ECR images")
    trivy_scan_failure_count = 0

    # Binary scanning logic
    for region, image_tag, image_uri, repo_name, image_digest in ecr_images:
        try:
            sync_single_image(
                neo4j_session,
                image_tag,
                image_uri,
                repo_name,
                image_digest,
                update_tag,
                True,
                trivy_path,
                trivy_opa_policy_file_path,
            )
        except subprocess.CalledProcessError as exc:
            trivy_error_msg = (
                exc.output.decode("utf-8") if type(exc.output) is bytes else exc.output
            )
            if "rego_parse_error" in trivy_error_msg:
                logger.error(
                    "Trivy image scan failed due to rego_parse_error - please check rego syntax! "
                    f"image_uri = {image_uri}, "
                    f"trivy_error_msg = {trivy_error_msg}.",
                )
                raise
            else:
                trivy_scan_failure_count += 1
                logger.warning(
                    "Trivy image scan failed - please investigate. trivy_scan_failure_count++."
                    f"image_uri = {image_uri}"
                    f"trivy_error_msg = {trivy_error_msg}.",
                )
                if (
                    trivy_scan_failure_count / num_images
                ) * 100 >= TRIVY_SCAN_FATAL_CIRCUIT_BREAKER_PERCENT:
                    logger.error(
                        "Trivy scan fatal failure circuit breaker hit, crashing."
                    )
                    raise
                # Else if circuit breaker is not hit, then keep going.
        except KeyError:
            trivy_scan_failure_count += 1
            logger.warning(
                "Trivy image scan failed because it returned unexpectedly incomplete data. "
                "Please repro locally. trivy_scan_failure_count++. "
                f"image_uri = {image_uri}.",
            )
            if (
                trivy_scan_failure_count / num_images
            ) * 100 >= TRIVY_SCAN_FATAL_CIRCUIT_BREAKER_PERCENT:
                logger.error("Trivy scan fatal failure circuit breaker hit, crashing.")
                raise
            # Else if circuit breaker is not hit, then keep going.

    cleanup(neo4j_session, common_job_parameters)


@timeit
def start_trivy_ingestion(neo4j_session: Session, config: Config) -> None:
    if not config.trivy_path:
        logger.info("Trivy module not configured. Skipping.")
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    # Check if S3 configuration is provided
    use_s3_scanning = config.trivy_s3_bucket and config.trivy_s3_prefix

    # Only update DB if not using S3 scanning
    if not use_s3_scanning:
        _call_trivy_update_db(config.trivy_path)

    if config.trivy_resource_type == "aws.ecr":
        if use_s3_scanning:
            # S3 scanning path
            ecr_images = get_scan_targets(neo4j_session)
            boto3_session = boto3.Session()

            sync_trivy_aws_ecr_from_s3(
                neo4j_session,
                ecr_images,
                config.trivy_s3_bucket,
                config.trivy_s3_prefix,
                config.update_tag,
                common_job_parameters,
                boto3_session,
            )
        else:
            # Binary scanning path
            sync_trivy_aws_ecr(
                neo4j_session,
                config.trivy_path,
                config.trivy_opa_policy_file_path,
                config.update_tag,
                common_job_parameters,
            )

    # Support other Trivy resource types here e.g. if Google Cloud has images.
