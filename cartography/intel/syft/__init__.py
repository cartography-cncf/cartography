"""
Syft intel module for enriching TrivyPackage nodes with dependency information.

This module ingests Syft's native JSON format to create DEPENDS_ON relationships
between TrivyPackage nodes, enabling CVE -> dependency chain tracing for remediation.

Direct vs transitive dependencies are derivable from the graph structure:
- Direct deps: packages with no incoming DEPENDS_ON edges (nothing depends on them)
- Transitive deps: packages that have incoming DEPENDS_ON edges

Usage:
    Syft should be run AFTER Trivy to enrich existing TrivyPackage nodes.
    The module matches packages by normalized_id for cross-tool compatibility.

File Naming Convention:
    - Syft JSON files should be named *.json
    - For pairing with Trivy: use matching base names (e.g., myimage.json for both)
"""

import json
import logging
import os
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError
from botocore.exceptions import ClientError
from neo4j import Session

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.config import Config
from cartography.graph.job import GraphJob
from cartography.intel.syft.parser import SyftValidationError
from cartography.intel.syft.parser import transform_artifacts
from cartography.intel.syft.parser import transform_dependencies
from cartography.intel.syft.parser import validate_syft_json
from cartography.models.syft import SyftPackageDependsOnMatchLink
from cartography.models.syft import SyftPackageSchema
from cartography.stats import get_stats_client
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


class SyftIngestionError(RuntimeError):
    """Raised when one or more Syft result objects fail to load."""


@timeit
def _load_packages(
    neo4j_session: Session,
    packages: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Create SyftPackage nodes with DEPENDS_ON relationships between them.

    Args:
        neo4j_session: Neo4j session
        packages: List of package dicts from transform_artifacts()
        update_tag: Update timestamp
    """
    if not packages:
        return

    load(neo4j_session, SyftPackageSchema(), packages, lastupdated=update_tag)
    logger.info("Created %d SyftPackage nodes", len(packages))


@timeit
def _load_dependencies(
    neo4j_session: Session,
    dependencies: list[dict[str, Any]],
    update_tag: int,
    sub_resource_label: str,
    sub_resource_id: str,
) -> None:
    """
    Create DEPENDS_ON relationships between TrivyPackage nodes.

    Args:
        neo4j_session: Neo4j session
        dependencies: List of dicts with 'source_id' and 'target_id' keys
        update_tag: Update timestamp
        sub_resource_label: Label of the sub-resource for scoped cleanup
        sub_resource_id: ID of the sub-resource for scoped cleanup
    """
    if not dependencies:
        return

    matchlink = SyftPackageDependsOnMatchLink()
    load_matchlinks(
        neo4j_session,
        matchlink,
        dependencies,
        lastupdated=update_tag,
        _sub_resource_label=sub_resource_label,
        _sub_resource_id=sub_resource_id,
    )
    logger.info(
        "Created %d DEPENDS_ON relationships between TrivyPackage nodes",
        len(dependencies),
    )


@timeit
def sync_single_syft(
    neo4j_session: Session,
    data: dict[str, Any],
    update_tag: int,
    sub_resource_label: str,
    sub_resource_id: str,
) -> None:
    """
    Process a single Syft JSON result and create DEPENDS_ON relationships.

    Args:
        neo4j_session: Neo4j session
        data: Parsed Syft JSON data
        update_tag: Update timestamp
        sub_resource_label: Label of the sub-resource (e.g., "AWSAccount")
        sub_resource_id: ID of the sub-resource (e.g., account ID)
    """
    validate_syft_json(data)

    # Transform and load SyftPackage nodes with self-referential DEPENDS_ON
    packages = transform_artifacts(data)
    _load_packages(neo4j_session, packages, update_tag)

    # Transform and load DEPENDS_ON MatchLinks between TrivyPackage nodes
    dependencies = transform_dependencies(data)
    _load_dependencies(
        neo4j_session,
        dependencies,
        update_tag,
        sub_resource_label,
        sub_resource_id,
    )

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


def _get_json_files_in_s3(
    s3_bucket: str, s3_prefix: str, boto3_session: boto3.Session
) -> set[str]:
    """
    List S3 objects in the S3 prefix.

    Args:
        s3_bucket: S3 bucket name
        s3_prefix: S3 prefix path
        boto3_session: boto3 session

    Returns:
        Set of S3 object keys for JSON files
    """
    s3_client = boto3_session.client("s3")
    results = set()

    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=s3_bucket, Prefix=s3_prefix)

        for page in page_iterator:
            if "Contents" not in page:
                continue

            for obj in page["Contents"]:
                object_key = obj["Key"]
                if object_key.endswith(".json") and object_key.startswith(s3_prefix):
                    results.add(object_key)

    except Exception as e:
        logger.error(
            "Error listing S3 objects in bucket %s with prefix %s: %s",
            s3_bucket,
            s3_prefix,
            e,
        )
        raise

    logger.info("Found %d json files in s3://%s/%s", len(results), s3_bucket, s3_prefix)
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
        common_job_parameters: Common job parameters (must include sub-resource info)
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

    # Extract sub-resource info from common_job_parameters
    # Default to a generic "SyftSync" scope if not provided
    sub_resource_label = common_job_parameters.get("_sub_resource_label", "SyftSync")
    sub_resource_id = common_job_parameters.get("_sub_resource_id", "default")

    logger.info("Processing %d local Syft result files", len(json_files))
    failed_files: list[str] = []

    for file_path in json_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                syft_data = json.load(f)
            sync_single_syft(
                neo4j_session,
                syft_data,
                update_tag,
                sub_resource_label,
                sub_resource_id,
            )
        except (OSError, json.JSONDecodeError, SyftValidationError) as e:
            logger.error("Failed to process Syft file %s: %s", file_path, e)
            failed_files.append(file_path)
            continue

    if failed_files:
        raise SyftIngestionError(
            f"Failed to process {len(failed_files)} Syft file(s) from {results_dir}. "
            "Skipping cleanup to avoid deleting valid relationships."
        )

    cleanup_syft(neo4j_session, sub_resource_label, sub_resource_id, update_tag)


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

    json_files = _get_json_files_in_s3(syft_s3_bucket, syft_s3_prefix, boto3_session)

    if not json_files:
        logger.warning(
            "Syft sync was configured, but no json files were found in bucket "
            "'%s' with prefix '%s'. This is OK if you only ran Trivy without Syft.",
            syft_s3_bucket,
            syft_s3_prefix,
        )
        return

    # Extract sub-resource info
    sub_resource_label = common_job_parameters.get("_sub_resource_label", "SyftSync")
    sub_resource_id = common_job_parameters.get("_sub_resource_id", "default")

    logger.info("Processing %d Syft result files from S3", len(json_files))
    s3_client = boto3_session.client("s3")
    failed_objects: list[str] = []

    for s3_object_key in json_files:
        logger.debug(
            "Reading scan results from S3: s3://%s/%s", syft_s3_bucket, s3_object_key
        )
        try:
            response = s3_client.get_object(Bucket=syft_s3_bucket, Key=s3_object_key)
            scan_data_json = response["Body"].read().decode("utf-8")
            syft_data = json.loads(scan_data_json)
            sync_single_syft(
                neo4j_session,
                syft_data,
                update_tag,
                sub_resource_label,
                sub_resource_id,
            )
        except (
            BotoCoreError,
            ClientError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            KeyError,
            SyftValidationError,
        ) as e:
            logger.error(
                "Failed to process Syft data from s3://%s/%s: %s",
                syft_s3_bucket,
                s3_object_key,
                e,
            )
            failed_objects.append(s3_object_key)
            continue

    if failed_objects:
        raise SyftIngestionError(
            f"Failed to process {len(failed_objects)} Syft object(s) from "
            f"s3://{syft_s3_bucket}/{syft_s3_prefix}. "
            "Skipping cleanup to avoid deleting valid relationships."
        )

    cleanup_syft(neo4j_session, sub_resource_label, sub_resource_id, update_tag)


@timeit
def cleanup_syft(
    neo4j_session: Session,
    sub_resource_label: str,
    sub_resource_id: str,
    update_tag: int,
) -> None:
    """
    Run cleanup for Syft-created DEPENDS_ON relationships.

    Args:
        neo4j_session: Neo4j session
        sub_resource_label: Label of the sub-resource for scoped cleanup
        sub_resource_id: ID of the sub-resource for scoped cleanup
        update_tag: Update timestamp
    """
    logger.info("Running Syft cleanup")
    # Clean up SyftPackage nodes (unscoped, uses UPDATE_TAG)
    GraphJob.from_node_schema(
        SyftPackageSchema(),
        {"UPDATE_TAG": update_tag},
    ).run(neo4j_session)

    # Clean up TrivyPackage DEPENDS_ON MatchLinks (scoped)
    matchlink = SyftPackageDependsOnMatchLink()
    cleanup_job = GraphJob.from_matchlink(
        matchlink, sub_resource_label, sub_resource_id, update_tag
    )
    cleanup_job.run(neo4j_session)


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
        # Use a generic sub-resource scope for Syft
        # This allows cleanup to work across all Syft-created relationships
        "_sub_resource_label": "SyftSync",
        "_sub_resource_id": "default",
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
