import json
import logging
from typing import Any

import boto3
from neo4j import Session

from cartography.config import Config
from cartography.intel.docker_scout.scanner import cleanup
from cartography.intel.docker_scout.scanner import sync_from_file
from cartography.intel.trivy.scanner import get_json_files_in_dir
from cartography.intel.trivy.scanner import get_json_files_in_s3
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_docker_scout_from_dir(
    neo4j_session: Session,
    results_dir: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """Sync Docker Scout scan results from local JSON files."""
    logger.info("Using Docker Scout scan results from %s", results_dir)

    json_files = get_json_files_in_dir(results_dir)

    if not json_files:
        logger.error(
            "Docker Scout sync was configured, but no json files were found in %s.",
            results_dir,
        )
        raise ValueError("No Docker Scout json results found on disk")

    logger.info("Processing %d local Docker Scout result files", len(json_files))

    synced_count = 0
    for file_path in json_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                scout_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse Docker Scout JSON from {file_path}"
            ) from e
        if sync_from_file(neo4j_session, scout_data, file_path, update_tag):
            synced_count += 1

    if synced_count > 0:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "No Docker Scout files were successfully processed, skipping cleanup to preserve existing data",
        )


@timeit
def sync_docker_scout_from_s3(
    neo4j_session: Session,
    s3_bucket: str,
    s3_prefix: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    boto3_session: boto3.Session,
) -> None:
    """Sync Docker Scout scan results from S3."""
    logger.info("Using Docker Scout scan results from s3://%s/%s", s3_bucket, s3_prefix)

    json_files = get_json_files_in_s3(s3_bucket, s3_prefix, boto3_session)

    if not json_files:
        logger.error(
            "Docker Scout sync was configured, but no json files found in s3://%s/%s.",
            s3_bucket,
            s3_prefix,
        )
        raise ValueError("No Docker Scout json results found in S3")

    logger.info("Processing %d S3 Docker Scout result files", len(json_files))

    synced_count = 0
    s3_client = boto3_session.client("s3")
    for s3_key in json_files:
        response = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        raw = response["Body"].read().decode("utf-8")
        try:
            scout_data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse Docker Scout JSON from s3://{s3_bucket}/{s3_key}"
            ) from e

        if sync_from_file(
            neo4j_session, scout_data, f"s3://{s3_bucket}/{s3_key}", update_tag
        ):
            synced_count += 1

    if synced_count > 0:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "No Docker Scout files were successfully processed, skipping cleanup to preserve existing data",
        )


@timeit
def start_docker_scout_ingestion(neo4j_session: Session, config: Config) -> None:
    """Entry point for Docker Scout ingestion.

    Supports two modes (checked in priority order):
    1. Local directory with pre-generated JSON files (--docker-scout-results-dir)
    2. S3 bucket with pre-generated JSON files (--docker-scout-s3-bucket)
    """
    if not config.docker_scout_results_dir and not config.docker_scout_s3_bucket:
        logger.info(
            "Docker Scout configuration not provided. Skipping Docker Scout ingestion."
        )
        return

    common_job_parameters = {"UPDATE_TAG": config.update_tag}

    # Priority 1: Local directory
    if config.docker_scout_results_dir:
        sync_docker_scout_from_dir(
            neo4j_session,
            config.docker_scout_results_dir,
            config.update_tag,
            common_job_parameters,
        )
        return

    # Priority 2: S3 bucket
    s3_prefix = config.docker_scout_s3_prefix or ""
    sync_docker_scout_from_s3(
        neo4j_session,
        config.docker_scout_s3_bucket,
        s3_prefix,
        config.update_tag,
        common_job_parameters,
        boto3.Session(),
    )
