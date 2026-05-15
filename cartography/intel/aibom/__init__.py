import logging
from typing import Any

import boto3
from neo4j import Session

from cartography.config import Config
from cartography.intel.aibom.cleanup import cleanup_aibom
from cartography.intel.aibom.loader import load_aibom_document
from cartography.intel.aibom.parser import parse_aibom_document
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
from cartography.stats import get_stats_client
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def sync_aibom_from_report_reader(
    neo4j_session: Session,
    reader: ReportReader,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Using AIBOM results from %s", reader.source_uri)

    json_files = filter_report_refs(
        reader.list_reports(),
        suffix=".json",
    )
    if not json_files:
        logger.warning(
            "AIBOM sync was configured, but no json files were found in %s",
            reader.source_uri,
        )
        return

    failed_report_count = 0
    processed_reports = 0
    for ref in json_files:
        source = ref.uri
        try:
            document = read_json_report(reader, ref)
        except ObjectStoreError as exc:
            logger.error("Failed to read AIBOM data from %s: %s", source, exc)
            failed_report_count += 1
            continue

        if not isinstance(document, dict):
            logger.warning("Skipping AIBOM report %s: expected JSON object", source)
            continue

        try:
            parsed_document = parse_aibom_document(document, report_location=source)
        except ValueError as exc:
            logger.warning("Skipping invalid AIBOM report %s: %s", source, exc)
            continue

        if not parsed_document.sources:
            logger.info("AIBOM report %s had no sources to ingest", source)
            continue

        stat_handler.incr("aibom_reports_processed")
        load_aibom_document(neo4j_session, parsed_document, update_tag)
        processed_reports += 1

    if failed_report_count:
        logger.warning(
            "Skipping AIBOM cleanup because %d report(s) failed to read or parse.",
            failed_report_count,
        )
        return

    # Skip cleanup when nothing was ingested: AIBOM cleanup is unscoped and
    # would delete data from a successful prior run.
    if processed_reports == 0:
        logger.warning(
            "Skipping AIBOM cleanup because no reports were ingested.",
        )
        return

    cleanup_aibom(neo4j_session, common_job_parameters)


@timeit
def sync_aibom_from_dir(
    neo4j_session: Session,
    results_dir: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    # DEPRECATED: sync_aibom_from_dir() will be removed in v1.0.0.
    sync_aibom_from_report_reader(
        neo4j_session,
        LocalReportReader(results_dir),
        update_tag,
        common_job_parameters,
    )


@timeit
def sync_aibom_from_s3(
    neo4j_session: Session,
    aibom_s3_bucket: str,
    aibom_s3_prefix: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    boto3_session: boto3.Session,
) -> None:
    # DEPRECATED: sync_aibom_from_s3() will be removed in v1.0.0.
    with S3BucketReader(
        boto3_session,
        aibom_s3_bucket,
        aibom_s3_prefix,
    ) as reader:
        sync_aibom_from_report_reader(
            neo4j_session,
            reader,
            update_tag=update_tag,
            common_job_parameters=common_job_parameters,
        )


@timeit
def start_aibom_ingestion(neo4j_session: Session, config: Config) -> None:
    if not config.aibom_source:
        logger.info("AIBOM configuration not provided. Skipping AIBOM ingestion.")
        return

    source = parse_report_source(config.aibom_source)
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }
    with build_report_reader_for_source(
        source,
        config=config,
    ) as reader:
        sync_aibom_from_report_reader(
            neo4j_session,
            reader,
            config.update_tag,
            common_job_parameters,
        )
