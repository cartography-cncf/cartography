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

import json
import logging
import os
from typing import Any

import boto3
from neo4j import Session

from cartography.client.core.tx import load
from cartography.config import Config
from cartography.graph.job import GraphJob
from cartography.intel.common.object_store import filter_object_refs
from cartography.intel.common.object_store import read_json_document
from cartography.intel.common.object_store import S3BucketReader
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


def _get_json_files_in_dir(results_dir: str) -> set[str]:
    """Return set of JSON file paths under a directory."""
    results = set()
    for root, _dirs, files in os.walk(results_dir):
        for filename in files:
            if filename.endswith(".json"):
                results.add(os.path.join(root, filename))
    logger.info("Found %d json files in %s", len(results), results_dir)
    return results


@timeit
def sync_syft_from_dir(
    neo4j_session: Session,
    results_dir: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Syft results from a local directory.

    Args:
        neo4j_session: Neo4j session
        results_dir: Path to directory containing Syft JSON files
        update_tag: Update timestamp
        common_job_parameters: Common job parameters
    """
    logger.info("Using Syft scan results from %s", results_dir)

    json_files = _get_json_files_in_dir(results_dir)

    if not json_files:
        logger.warning(
            "Syft sync was configured, but no json files were found in %s. "
            "This is OK if you only ran Trivy without Syft.",
            results_dir,
        )
        return

    logger.info("Processing %d local Syft result files", len(json_files))

    for file_path in json_files:
        with open(file_path, encoding="utf-8") as f:
            syft_data = json.load(f)
        sync_single_syft(
            neo4j_session,
            syft_data,
            update_tag,
        )

    cleanup_syft(neo4j_session, update_tag)


@timeit
def sync_syft_from_s3(
    neo4j_session: Session,
    syft_s3_bucket: str,
    syft_s3_prefix: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    boto3_session: boto3.Session,
) -> None:
    """
    Sync Syft results from S3.

    Args:
        neo4j_session: Neo4j session
        syft_s3_bucket: S3 bucket name
        syft_s3_prefix: S3 prefix path
        update_tag: Update timestamp
        common_job_parameters: Common job parameters
        boto3_session: boto3 session for S3 operations
    """
    logger.info(
        "Using Syft scan results from s3://%s/%s", syft_s3_bucket, syft_s3_prefix
    )

    reader = S3BucketReader(boto3_session)
    json_files = filter_object_refs(
        reader.list_objects(syft_s3_bucket, syft_s3_prefix),
        suffix=".json",
    )

    if not json_files:
        logger.warning(
            "Syft sync was configured, but no json files were found in bucket "
            "'%s' with prefix '%s'. This is OK if you only ran Trivy without Syft.",
            syft_s3_bucket,
            syft_s3_prefix,
        )
        return

    logger.info("Processing %d Syft result files from S3", len(json_files))

    for ref in json_files:
        logger.debug(
            "Reading scan results from S3: %s",
            ref.uri,
        )
        syft_data = read_json_document(reader, ref)
        sync_single_syft(
            neo4j_session,
            syft_data,
            update_tag,
        )

    cleanup_syft(neo4j_session, update_tag)


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
        config: Configuration object with syft_results_dir or syft_s3_bucket/prefix
    """
    if not config.syft_s3_bucket and not config.syft_results_dir:
        logger.info("Syft configuration not provided. Skipping Syft ingestion.")
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    if config.syft_results_dir:
        sync_syft_from_dir(
            neo4j_session,
            config.syft_results_dir,
            config.update_tag,
            common_job_parameters,
        )
        return

    if config.syft_s3_bucket:
        syft_s3_prefix = config.syft_s3_prefix if config.syft_s3_prefix else ""

        boto3_session = boto3.Session()

        sync_syft_from_s3(
            neo4j_session,
            config.syft_s3_bucket,
            syft_s3_prefix,
            config.update_tag,
            common_job_parameters,
            boto3_session,
        )
