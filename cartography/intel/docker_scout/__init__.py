import logging
from pathlib import Path
from typing import Any

import boto3
from neo4j import Session

from cartography.config import Config
from cartography.intel.common.object_store import BucketReader
from cartography.intel.common.object_store import ObjectStoreParseError
from cartography.intel.common.object_store import read_text_document
from cartography.intel.common.object_store import S3BucketReader
from cartography.intel.common.report_source import build_bucket_reader_for_source
from cartography.intel.common.report_source import LocalReportSource
from cartography.intel.common.report_source import parse_report_source
from cartography.intel.docker_scout.scanner import cleanup
from cartography.intel.docker_scout.scanner import sync_from_file
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
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "No Docker Scout files were successfully processed, skipping cleanup to preserve existing data",
        )


@timeit
def sync_docker_scout_from_bucket_reader(
    neo4j_session: Session,
    source_uri: str,
    reader: BucketReader,
    bucket_name: str,
    prefix: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Using Docker Scout recommendation reports from %s", source_uri)

    report_refs = sorted(
        reader.list_objects(bucket_name, prefix),
        key=lambda ref: ref.key,
    )
    if not report_refs:
        logger.error(
            "Docker Scout sync was configured, but no report files found in %s.",
            source_uri,
        )
        raise ValueError("No Docker Scout recommendation reports found in object store")

    logger.info(
        "Processing %d Docker Scout report files from object store",
        len(report_refs),
    )

    synced_count = 0
    for ref in report_refs:
        try:
            raw_recommendation = read_text_document(reader, ref)
        except ObjectStoreParseError:
            logger.warning(
                "Skipping unreadable Docker Scout report %s",
                ref.uri,
            )
            continue
        if not _looks_like_docker_scout_report(raw_recommendation):
            logger.debug(
                "Skipping %s: not a Docker Scout recommendation report",
                ref.uri,
            )
            continue
        if sync_from_file(
            neo4j_session,
            raw_recommendation,
            ref.uri,
            update_tag,
        ):
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
    sync_docker_scout_from_bucket_reader(
        neo4j_session,
        source_uri=f"s3://{s3_bucket}/{s3_prefix}",
        reader=S3BucketReader(boto3_session),
        bucket_name=s3_bucket,
        prefix=s3_prefix,
        update_tag=update_tag,
        common_job_parameters=common_job_parameters,
    )


@timeit
def start_docker_scout_ingestion(neo4j_session: Session, config: Config) -> None:
    """Entry point for Docker Scout ingestion from recommendation text reports."""
    if not config.docker_scout_source:
        logger.info(
            "Docker Scout configuration not provided. Skipping Docker Scout ingestion."
        )
        return

    source = parse_report_source(config.docker_scout_source)
    common_job_parameters = {"UPDATE_TAG": config.update_tag}

    if isinstance(source, LocalReportSource):
        sync_docker_scout_from_dir(
            neo4j_session,
            source.path,
            config.update_tag,
            common_job_parameters,
        )
        return

    reader, bucket_name, prefix = build_bucket_reader_for_source(
        source,
        azure_sp_auth=config.azure_sp_auth,
        azure_tenant_id=config.azure_tenant_id,
        azure_client_id=config.azure_client_id,
        azure_client_secret=config.azure_client_secret,
    )
    sync_docker_scout_from_bucket_reader(
        neo4j_session,
        source.uri,
        reader,
        bucket_name,
        prefix,
        config.update_tag,
        common_job_parameters,
    )
