import logging
import os
from collections.abc import Iterator
from typing import Any

import boto3
from neo4j import Session

from cartography.config import Config
from cartography.intel.aibom.cleanup import cleanup_aibom
from cartography.intel.aibom.loader import load_aibom_document
from cartography.intel.aibom.parser import parse_aibom_document
from cartography.intel.common.object_store import filter_report_refs
from cartography.intel.common.object_store import ListedReportReader
from cartography.intel.common.object_store import LocalReportReader
from cartography.intel.common.object_store import ObjectStoreParseError
from cartography.intel.common.object_store import read_json_report
from cartography.intel.common.object_store import ReportReader
from cartography.intel.common.object_store import ReportRef
from cartography.intel.common.object_store import S3BucketReader
from cartography.intel.common.report_source import build_report_reader_for_source
from cartography.intel.common.report_source import parse_report_source
from cartography.stats import get_stats_client
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


def _get_json_files_in_dir(results_dir: str) -> set[str]:
    results: set[str] = set()
    for root, _dirs, files in os.walk(results_dir):
        for filename in files:
            if filename.endswith(".json"):
                results.add(os.path.join(root, filename))
    logger.info("Found %d AIBOM json files in %s", len(results), results_dir)
    return results


def _iter_documents_from_report_reader(
    json_files: list[ReportRef],
    reader: ReportReader,
) -> Iterator[tuple[str, dict[str, Any]]]:
    """Yield (source_label, document) pairs from report source documents."""
    for ref in json_files:
        source = ref.uri
        try:
            document = read_json_report(reader, ref)
        except ObjectStoreParseError as exc:
            logger.warning("Skipping unreadable AIBOM report %s: %s", source, exc)
            continue

        if not isinstance(document, dict):
            logger.warning("Skipping AIBOM report %s: expected JSON object", source)
            continue

        yield source, document


def _ingest_aibom_reports(
    neo4j_session: Session,
    documents: Iterator[tuple[str, dict[str, Any]]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """Ingest AIBOM documents and run cleanup if any were processed."""
    processed_reports = 0
    for source, document in documents:
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

    # Only run cleanup when at least one report was ingested. Because AIBOM
    # cleanup is unscoped, running it after a batch where every document was
    # skipped (decode errors, unmatched images, etc.) would delete previously
    # ingested data from a successful prior run.
    if processed_reports:
        cleanup_aibom(neo4j_session, common_job_parameters)


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

    _ingest_aibom_reports(
        neo4j_session,
        _iter_documents_from_report_reader(json_files, reader),
        update_tag,
        common_job_parameters,
    )


@timeit
def sync_aibom_from_dir(
    neo4j_session: Session,
    results_dir: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    # DEPRECATED: sync_aibom_from_dir() will be removed in v1.0.0.
    reader = LocalReportReader(results_dir)
    refs = [
        ReportRef(
            uri=file_path,
            name=os.path.relpath(file_path, results_dir),
        )
        for file_path in _get_json_files_in_dir(results_dir)
    ]
    sync_aibom_from_report_reader(
        neo4j_session,
        ListedReportReader(results_dir, refs, reader.read_bytes),
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
    sync_aibom_from_report_reader(
        neo4j_session,
        S3BucketReader(
            boto3_session,
            aibom_s3_bucket,
            aibom_s3_prefix,
        ),
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
    reader = build_report_reader_for_source(
        source,
        azure_sp_auth=config.azure_sp_auth,
        azure_tenant_id=config.azure_tenant_id,
        azure_client_id=config.azure_client_id,
        azure_client_secret=config.azure_client_secret,
    )
    sync_aibom_from_report_reader(
        neo4j_session,
        reader,
        config.update_tag,
        common_job_parameters,
    )
