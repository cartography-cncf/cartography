import logging
from typing import Any

import boto3
from neo4j import Session

from cartography.config import Config
from cartography.intel.common.object_store import LocalReportReader
from cartography.intel.common.object_store import ObjectStoreError
from cartography.intel.common.object_store import read_text_report
from cartography.intel.common.object_store import ReportReader
from cartography.intel.common.object_store import S3BucketReader
from cartography.intel.common.report_reader_builder import (
    build_report_reader_for_source,
)
from cartography.intel.common.report_source import parse_report_source
from cartography.intel.docker_scout.scanner import cleanup
from cartography.intel.docker_scout.scanner import sync_from_file
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _looks_like_docker_scout_report(text: str) -> bool:
    required_markers = ("Target", "digest", "Base image is")
    return all(marker in text for marker in required_markers)


@timeit
def sync_docker_scout_from_report_reader(
    neo4j_session: Session,
    reader: ReportReader,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Using Docker Scout recommendation reports from %s", reader.source_uri)

    report_refs = sorted(
        reader.list_reports(),
        key=lambda ref: ref.name,
    )
    if not report_refs:
        logger.error(
            "Docker Scout sync was configured, but no report files were found in %s.",
            reader.source_uri,
        )
        raise ValueError(
            "No Docker Scout recommendation reports found in report source"
        )

    logger.info(
        "Processing %d Docker Scout report files from report source",
        len(report_refs),
    )

    failed_report_count = 0
    synced_count = 0
    for ref in report_refs:
        try:
            raw_recommendation = read_text_report(reader, ref)
        except ObjectStoreError as exc:
            logger.error("Failed to read Docker Scout report from %s: %s", ref.uri, exc)
            failed_report_count += 1
            continue
        if not _looks_like_docker_scout_report(raw_recommendation):
            logger.debug(
                "Skipping %s: not a Docker Scout recommendation report",
                ref.uri,
            )
            continue
        if sync_from_file(neo4j_session, raw_recommendation, ref.uri, update_tag):
            synced_count += 1

    if failed_report_count:
        logger.warning(
            "Skipping Docker Scout cleanup because %d report(s) failed to read or parse.",
            failed_report_count,
        )
        return

    if synced_count == 0:
        logger.warning(
            "Skipping Docker Scout cleanup because no reports were ingested.",
        )
        return

    cleanup(neo4j_session, common_job_parameters)


@timeit
def sync_docker_scout_from_dir(
    neo4j_session: Session,
    results_dir: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    # DEPRECATED: sync_docker_scout_from_dir() will be removed in v1.0.0.
    sync_docker_scout_from_report_reader(
        neo4j_session,
        LocalReportReader(results_dir),
        update_tag,
        common_job_parameters,
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
    # DEPRECATED: sync_docker_scout_from_s3() will be removed in v1.0.0.
    with S3BucketReader(
        boto3_session,
        s3_bucket,
        s3_prefix,
    ) as reader:
        sync_docker_scout_from_report_reader(
            neo4j_session,
            reader=reader,
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

    with build_report_reader_for_source(
        source,
        config=config,
    ) as reader:
        sync_docker_scout_from_report_reader(
            neo4j_session,
            reader,
            config.update_tag,
            common_job_parameters,
        )
