import logging
from pathlib import Path
from typing import Any

import boto3
from neo4j import Session

from cartography.config import Config
from cartography.intel.docker_scout.scanner import cleanup
from cartography.intel.docker_scout.scanner import sync_from_file
from cartography.util import run_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _looks_like_docker_scout_report(text: str) -> bool:
    required_markers = ("Target", "digest", "Base image is")
    return all(marker in text for marker in required_markers)


def _get_report_files_in_dir(results_dir: str) -> list[str]:
    return sorted(
        str(path)
        for path in Path(results_dir).rglob("*")
        if path.is_file() and not path.name.startswith(".")
    )


def _get_report_files_in_s3(
    s3_bucket: str,
    s3_prefix: str,
    boto3_session: boto3.Session,
) -> list[str]:
    client = boto3_session.client("s3")
    paginator = client.get_paginator("list_objects_v2")
    keys: list[str] = []
    for page in paginator.paginate(Bucket=s3_bucket, Prefix=s3_prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.endswith("/"):
                keys.append(key)
    return sorted(keys)


@timeit
def sync_docker_scout_from_dir(
    neo4j_session: Session,
    results_dir: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Using Docker Scout recommendation reports from %s", results_dir)

    report_files = _get_report_files_in_dir(results_dir)
    if not report_files:
        logger.error(
            "Docker Scout sync was configured, but no report files were found in %s.",
            results_dir,
        )
        raise ValueError("No Docker Scout recommendation reports found on disk")

    logger.info("Processing %d local Docker Scout report files", len(report_files))

    synced_count = 0
    for file_path in report_files:
        try:
            raw_recommendation = Path(file_path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.warning("Skipping unreadable Docker Scout report %s", file_path)
            continue
        if not _looks_like_docker_scout_report(raw_recommendation):
            logger.debug(
                "Skipping %s: not a Docker Scout recommendation report", file_path
            )
            continue
        if sync_from_file(neo4j_session, raw_recommendation, file_path, update_tag):
            synced_count += 1

    if synced_count > 0:
        run_analysis_job(
            "docker_scout_parent_image_built_on.json",
            neo4j_session,
            common_job_parameters,
        )
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
    logger.info(
        "Using Docker Scout recommendation reports from s3://%s/%s",
        s3_bucket,
        s3_prefix,
    )

    report_files = _get_report_files_in_s3(s3_bucket, s3_prefix, boto3_session)
    if not report_files:
        logger.error(
            "Docker Scout sync was configured, but no report files found in s3://%s/%s.",
            s3_bucket,
            s3_prefix,
        )
        raise ValueError("No Docker Scout recommendation reports found in S3")

    logger.info("Processing %d S3 Docker Scout report files", len(report_files))

    synced_count = 0
    s3_client = boto3_session.client("s3")
    for s3_key in report_files:
        response = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        try:
            raw_recommendation = response["Body"].read().decode("utf-8")
        except UnicodeDecodeError:
            logger.warning(
                "Skipping unreadable Docker Scout report s3://%s/%s",
                s3_bucket,
                s3_key,
            )
            continue
        if not _looks_like_docker_scout_report(raw_recommendation):
            logger.debug(
                "Skipping s3://%s/%s: not a Docker Scout recommendation report",
                s3_bucket,
                s3_key,
            )
            continue
        if sync_from_file(
            neo4j_session,
            raw_recommendation,
            f"s3://{s3_bucket}/{s3_key}",
            update_tag,
        ):
            synced_count += 1

    if synced_count > 0:
        run_analysis_job(
            "docker_scout_parent_image_built_on.json",
            neo4j_session,
            common_job_parameters,
        )
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "No Docker Scout files were successfully processed, skipping cleanup to preserve existing data",
        )


@timeit
def start_docker_scout_ingestion(neo4j_session: Session, config: Config) -> None:
    """Entry point for Docker Scout ingestion from recommendation text reports."""
    if not config.docker_scout_results_dir and not config.docker_scout_s3_bucket:
        logger.info(
            "Docker Scout configuration not provided. Skipping Docker Scout ingestion."
        )
        return

    common_job_parameters = {"UPDATE_TAG": config.update_tag}

    if config.docker_scout_results_dir:
        sync_docker_scout_from_dir(
            neo4j_session,
            config.docker_scout_results_dir,
            config.update_tag,
            common_job_parameters,
        )
        return

    s3_prefix = config.docker_scout_s3_prefix or ""
    sync_docker_scout_from_s3(
        neo4j_session,
        config.docker_scout_s3_bucket,
        s3_prefix,
        config.update_tag,
        common_job_parameters,
        boto3.Session(),
    )
