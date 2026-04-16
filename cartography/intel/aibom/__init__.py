import json
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
from cartography.intel.common.object_store import filter_object_refs
from cartography.intel.common.object_store import ObjectRef
from cartography.intel.common.object_store import ObjectStoreParseError
from cartography.intel.common.object_store import read_json_document
from cartography.intel.common.object_store import S3BucketReader
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


def _iter_documents_from_dir(
    json_files: set[str],
) -> Iterator[tuple[str, dict[str, Any]]]:
    """Yield (source_label, document) pairs from local JSON files."""
    for file_path in json_files:
        try:
            with open(file_path, encoding="utf-8") as file_pointer:
                document = json.load(file_pointer)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            logger.warning("Skipping unreadable AIBOM report %s: %s", file_path, exc)
            continue

        if not isinstance(document, dict):
            logger.warning("Skipping AIBOM report %s: expected JSON object", file_path)
            continue

        yield file_path, document


def _iter_documents_from_s3(
    json_files: list[ObjectRef],
    reader: S3BucketReader,
) -> Iterator[tuple[str, dict[str, Any]]]:
    """Yield (source_label, document) pairs from S3 objects."""
    for ref in json_files:
        source = ref.uri
        try:
            document = read_json_document(reader, ref)
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
def sync_aibom_from_dir(
    neo4j_session: Session,
    results_dir: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Using AIBOM results from %s", results_dir)

    json_files = _get_json_files_in_dir(results_dir)
    if not json_files:
        logger.warning(
            "AIBOM sync was configured, but no json files were found in %s",
            results_dir,
        )
        return

    _ingest_aibom_reports(
        neo4j_session,
        _iter_documents_from_dir(json_files),
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
    logger.info("Using AIBOM results from s3://%s/%s", aibom_s3_bucket, aibom_s3_prefix)

    reader = S3BucketReader(boto3_session)
    json_files = filter_object_refs(
        reader.list_objects(aibom_s3_bucket, aibom_s3_prefix),
        suffix=".json",
    )
    if not json_files:
        logger.warning(
            "AIBOM sync was configured, but no json files were found in bucket %s with prefix %s",
            aibom_s3_bucket,
            aibom_s3_prefix,
        )
        return

    _ingest_aibom_reports(
        neo4j_session,
        _iter_documents_from_s3(json_files, reader),
        update_tag,
        common_job_parameters,
    )


@timeit
def start_aibom_ingestion(neo4j_session: Session, config: Config) -> None:
    if not config.aibom_s3_bucket and not config.aibom_results_dir:
        logger.info("AIBOM configuration not provided. Skipping AIBOM ingestion.")
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    if config.aibom_results_dir:
        sync_aibom_from_dir(
            neo4j_session,
            config.aibom_results_dir,
            config.update_tag,
            common_job_parameters,
        )
        return

    if config.aibom_s3_bucket:
        aibom_s3_prefix = config.aibom_s3_prefix if config.aibom_s3_prefix else ""
        boto3_session = boto3.Session()
        sync_aibom_from_s3(
            neo4j_session,
            config.aibom_s3_bucket,
            aibom_s3_prefix,
            config.update_tag,
            common_job_parameters,
            boto3_session,
        )
