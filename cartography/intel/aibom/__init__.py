import json
import logging
import os
from typing import Any

import boto3
from neo4j import Session

from cartography.config import Config
from cartography.intel.aibom.cleanup import cleanup_aibom
from cartography.intel.aibom.loader import load_aibom_sources
from cartography.intel.aibom.parser import parse_aibom_document
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


def _get_json_files_in_s3(
    s3_bucket: str,
    s3_prefix: str,
    boto3_session: boto3.Session,
) -> set[str]:
    s3_client = boto3_session.client("s3")
    results: set[str] = set()

    paginator = s3_client.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(Bucket=s3_bucket, Prefix=s3_prefix)

    for page in page_iterator:
        if "Contents" not in page:
            continue

        for obj in page["Contents"]:
            object_key = obj["Key"]
            if object_key.endswith(".json") and object_key.startswith(s3_prefix):
                results.add(object_key)

    logger.info(
        "Found %d AIBOM json files in s3://%s/%s",
        len(results),
        s3_bucket,
        s3_prefix,
    )
    return results


def _ingest_aibom_document(
    neo4j_session: Session,
    document: dict[str, Any],
    update_tag: int,
    source: str,
) -> bool:
    try:
        parsed_sources = parse_aibom_document(document)
    except ValueError as exc:
        logger.warning("Skipping invalid AIBOM report %s: %s", source, exc)
        return False

    if not parsed_sources:
        logger.info("AIBOM report %s had no sources to ingest", source)
        return False

    stat_handler.incr("aibom_reports_processed")
    load_aibom_sources(neo4j_session, parsed_sources, update_tag)
    return True


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

    processed_reports = 0
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

        if _ingest_aibom_document(neo4j_session, document, update_tag, file_path):
            processed_reports += 1

    if processed_reports:
        cleanup_aibom(neo4j_session, common_job_parameters)


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

    json_files = _get_json_files_in_s3(aibom_s3_bucket, aibom_s3_prefix, boto3_session)
    if not json_files:
        logger.warning(
            "AIBOM sync was configured, but no json files were found in bucket %s with prefix %s",
            aibom_s3_bucket,
            aibom_s3_prefix,
        )
        return

    s3_client = boto3_session.client("s3")
    processed_reports = 0

    for object_key in json_files:
        try:
            response = s3_client.get_object(Bucket=aibom_s3_bucket, Key=object_key)
            scan_data_json = response["Body"].read().decode("utf-8")
            document = json.loads(scan_data_json)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            logger.warning(
                "Skipping unreadable AIBOM report s3://%s/%s: %s",
                aibom_s3_bucket,
                object_key,
                exc,
            )
            continue

        if not isinstance(document, dict):
            logger.warning(
                "Skipping AIBOM report s3://%s/%s: expected JSON object",
                aibom_s3_bucket,
                object_key,
            )
            continue

        source = f"s3://{aibom_s3_bucket}/{object_key}"
        if _ingest_aibom_document(neo4j_session, document, update_tag, source):
            processed_reports += 1

    if processed_reports:
        cleanup_aibom(neo4j_session, common_job_parameters)


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
