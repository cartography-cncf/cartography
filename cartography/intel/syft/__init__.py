"""
Syft intel module for creating SyftPackage nodes with dependency relationships.

This module ingests Syft's native JSON format to create SyftPackage nodes
with DEPENDS_ON relationships between them.

Direct vs transitive dependencies are derivable from the graph structure:
- Direct deps: packages with no incoming DEPENDS_ON edges (nothing depends on them)
- Transitive deps: packages that have incoming DEPENDS_ON edges

File Naming Convention:
    - Syft JSON files should be named *.json
"""

import logging
from typing import Any

import boto3
from neo4j import Session

from cartography.client.core.tx import load
from cartography.config import Config
from cartography.graph.job import GraphJob
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
from cartography.intel.syft.parser import transform_artifacts
from cartography.models.syft import SyftPackageSchema
from cartography.stats import get_stats_client
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def sync_single_syft(
    neo4j_session: Session,
    data: dict[str, Any],
    update_tag: int,
) -> None:
    """
    Process a single Syft JSON result and create SyftPackage nodes.

    Args:
        neo4j_session: Neo4j session
        data: Parsed Syft JSON data
        update_tag: Update timestamp
    """
    packages = transform_artifacts(data)
    if packages:
        load(neo4j_session, SyftPackageSchema(), packages, lastupdated=update_tag)

    stat_handler.incr("syft_files_processed")


@timeit
def sync_syft_from_report_reader(
    neo4j_session: Session,
    reader: ReportReader,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """Sync Syft results from a report reader."""
    logger.info("Using Syft scan results from %s", reader.source_uri)

    json_files = filter_report_refs(
        reader.list_reports(),
        suffix=".json",
    )

    if not json_files:
        logger.warning(
            "Syft sync was configured, but no json files were found in %s. "
            "This is OK if you only ran Trivy without Syft.",
            reader.source_uri,
        )
        return

    logger.info("Processing %d Syft result files from report source", len(json_files))
    failed_report_count = 0
    processed_reports = 0
    for ref in json_files:
        logger.debug(
            "Reading scan results from report source: %s",
            ref.uri,
        )
        try:
            syft_data = read_json_report(reader, ref)
        except ObjectStoreError as exc:
            logger.error("Failed to read Syft data from %s: %s", ref.uri, exc)
            failed_report_count += 1
            continue

        sync_single_syft(
            neo4j_session,
            syft_data,
            update_tag,
        )
        processed_reports += 1

    if failed_report_count:
        logger.warning(
            "Skipping Syft cleanup because %d report(s) failed to read or parse.",
            failed_report_count,
        )
        return

    if processed_reports == 0:
        logger.warning(
            "Skipping Syft cleanup because no reports were ingested.",
        )
        return

    cleanup_syft(neo4j_session, update_tag)


@timeit
def sync_syft_from_dir(
    neo4j_session: Session,
    results_dir: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    # DEPRECATED: sync_syft_from_dir() will be removed in v1.0.0.
    sync_syft_from_report_reader(
        neo4j_session,
        LocalReportReader(results_dir),
        update_tag,
        common_job_parameters,
    )


@timeit
def sync_syft_from_s3(
    neo4j_session: Session,
    syft_s3_bucket: str,
    syft_s3_prefix: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    boto3_session: boto3.Session,
) -> None:
    # DEPRECATED: sync_syft_from_s3() will be removed in v1.0.0.
    with S3BucketReader(
        boto3_session,
        syft_s3_bucket,
        syft_s3_prefix,
    ) as reader:
        sync_syft_from_report_reader(
            neo4j_session,
            reader=reader,
            update_tag=update_tag,
            common_job_parameters=common_job_parameters,
        )


@timeit
def cleanup_syft(
    neo4j_session: Session,
    update_tag: int,
) -> None:
    """
    Run cleanup for Syft-created SyftPackage nodes.

    Args:
        neo4j_session: Neo4j session
        update_tag: Update timestamp
    """
    logger.info("Running Syft cleanup")
    GraphJob.from_node_schema(
        SyftPackageSchema(),
        {"UPDATE_TAG": update_tag},
    ).run(neo4j_session)


@timeit
def start_syft_ingestion(neo4j_session: Session, config: Config) -> None:
    """
    Main entry point for Syft ingestion.

    Args:
        neo4j_session: Neo4j session
        config: Configuration object with syft_source
    """
    if not config.syft_source:
        logger.info("Syft configuration not provided. Skipping Syft ingestion.")
        return

    source = parse_report_source(config.syft_source)
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    with build_report_reader_for_source(
        source,
        config=config,
    ) as reader:
        sync_syft_from_report_reader(
            neo4j_session,
            reader,
            config.update_tag,
            common_job_parameters,
        )
