"""
Cartography SBOM Intel Module.

This module ingests CycloneDX SBOMs (from Syft) and enriches existing TrivyPackage nodes with:
- is_direct property (direct vs transitive dependencies)
- DEPENDS_ON relationships between packages (dependency graph)

This enables tracing from CVE → transitive dep → direct dep → actionable fix.

Architecture:
1. Trivy module runs first, creating TrivyPackage nodes with CVEs (TrivyImageFinding)
2. SBOM module runs after, enriching TrivyPackage nodes with dependency graph from Syft

Package ID format: {version}|{name} (matches Trivy's format)
"""

import json
import logging
import os
from typing import Any

import boto3
from neo4j import Session

from cartography.client.core.tx import load_matchlinks
from cartography.config import Config
from cartography.graph.job import GraphJob
from cartography.intel.sbom.parser import transform_sbom_dependencies
from cartography.intel.sbom.parser import transform_sbom_packages
from cartography.intel.sbom.parser import validate_cyclonedx_sbom
from cartography.models.sbom.dependency import TrivyPackageDependsOnMatchLink
from cartography.stats import get_stats_client
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


def get_json_files_in_s3(
    s3_bucket: str,
    s3_prefix: str,
    boto3_session: boto3.Session,
) -> set[str]:
    """
    List S3 objects in the S3 prefix.

    Args:
        s3_bucket: S3 bucket name containing SBOM files.
        s3_prefix: S3 prefix path containing SBOM files.
        boto3_session: boto3 session for S3 operations.

    Returns:
        Set of S3 object keys for JSON files in the S3 prefix.
    """
    s3_client = boto3_session.client("s3")

    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=s3_bucket, Prefix=s3_prefix)
        results = set()

        for page in page_iterator:
            if "Contents" not in page:
                continue

            for obj in page["Contents"]:
                object_key = obj["Key"]

                if not object_key.endswith(".json"):
                    continue

                if not object_key.startswith(s3_prefix):
                    continue

                results.add(object_key)

    except Exception as e:
        logger.error(
            "Error listing S3 objects in bucket %s with prefix %s: %s",
            s3_bucket,
            s3_prefix,
            e,
        )
        raise

    logger.debug(
        "Found %d JSON files in s3://%s/%s", len(results), s3_bucket, s3_prefix
    )
    return results


def get_json_files_in_dir(results_dir: str) -> set[str]:
    """Return set of JSON file paths under a directory."""
    results = set()
    for root, _dirs, files in os.walk(results_dir):
        for filename in files:
            if filename.endswith(".json"):
                results.add(os.path.join(root, filename))
    logger.debug("Found %d JSON files in %s", len(results), results_dir)
    return results


@timeit
def update_trivy_packages_is_direct(
    neo4j_session: Session,
    packages: list[dict[str, Any]],
    update_tag: int,
) -> int:
    """
    Update existing TrivyPackage nodes with is_direct property.

    This uses MERGE to update nodes that exist (created by Trivy module)
    and skips nodes that don't exist (packages not found by Trivy).

    Args:
        neo4j_session: Neo4j session for database operations.
        packages: List of package data with Trivy-compatible IDs.
        update_tag: Update tag for tracking.

    Returns:
        Number of TrivyPackage nodes updated.
    """
    if not packages:
        return 0

    # Update existing TrivyPackage nodes with is_direct property
    query = """
    UNWIND $packages AS pkg
    MATCH (p:TrivyPackage {id: pkg.id})
    SET p.is_direct = pkg.is_direct,
        p.lastupdated = $update_tag
    RETURN count(p) AS updated_count
    """

    result = neo4j_session.run(
        query,
        packages=packages,
        update_tag=update_tag,
    )
    record = result.single()
    updated_count = record["updated_count"] if record else 0

    logger.debug("Updated %d TrivyPackage nodes with is_direct property", updated_count)
    return updated_count


@timeit
def load_sbom_dependencies(
    neo4j_session: Session,
    dependencies: list[dict[str, Any]],
    source: str,
    update_tag: int,
) -> None:
    """
    Load DEPENDS_ON relationships between TrivyPackage nodes via MatchLink.

    Only creates relationships between existing TrivyPackage nodes.

    Args:
        neo4j_session: Neo4j session for database operations.
        dependencies: List of dependency relationships with Trivy-compatible IDs.
        source: Source identifier for sub-resource tracking in cleanup.
        update_tag: Update tag for tracking.
    """
    if not dependencies:
        logger.debug("No dependency relationships to load")
        return

    load_matchlinks(
        neo4j_session,
        TrivyPackageDependsOnMatchLink(),
        dependencies,
        lastupdated=update_tag,
        _sub_resource_label="SBOMSource",
        _sub_resource_id=source,
    )


@timeit
def sync_single_sbom(
    neo4j_session: Session,
    sbom_data: dict[str, Any],
    source: str,
    update_tag: int,
) -> None:
    """
    Sync a single SBOM to Neo4j by enriching existing TrivyPackage nodes.

    This function:
    1. Extracts package data with is_direct property from SBOM
    2. Updates existing TrivyPackage nodes with is_direct property
    3. Creates DEPENDS_ON relationships between TrivyPackage nodes

    TrivyPackage IDs are global ({version}|{name}), not image-scoped.
    The DEPLOYED relationship (from Trivy module) handles image association.

    Args:
        neo4j_session: Neo4j session for database operations.
        sbom_data: Raw CycloneDX SBOM data.
        source: Source identifier for logging (file path or S3 URI).
        update_tag: Update tag for tracking.
    """
    if not validate_cyclonedx_sbom(sbom_data):
        logger.warning("Skipping invalid SBOM from %s", source)
        return

    logger.info("Processing SBOM from %s", source)

    # Phase 1: Transform packages and update TrivyPackage nodes with is_direct
    packages = transform_sbom_packages(sbom_data)
    num_packages = len(packages)
    num_direct = sum(1 for p in packages if p.get("is_direct"))
    logger.debug(
        "Found %d packages (%d direct, %d transitive)",
        num_packages,
        num_direct,
        num_packages - num_direct,
    )

    updated_count = update_trivy_packages_is_direct(neo4j_session, packages, update_tag)
    stat_handler.incr("sbom_packages_enriched", updated_count)

    if updated_count == 0:
        logger.warning(
            "No TrivyPackage nodes were updated from SBOM %s. "
            "Ensure Trivy ingestion runs before SBOM ingestion.",
            source,
        )

    # Phase 2: Transform and load dependency relationships
    dependencies = transform_sbom_dependencies(sbom_data)
    logger.debug("Loading %d dependency relationships", len(dependencies))
    load_sbom_dependencies(neo4j_session, dependencies, source, update_tag)
    stat_handler.incr("sbom_dependencies_loaded", len(dependencies))

    stat_handler.incr("sbom_files_processed")
    logger.info(
        "Completed SBOM sync for %s: %d packages enriched, %d deps",
        source,
        updated_count,
        len(dependencies),
    )


@timeit
def cleanup_sbom_dependencies(
    neo4j_session: Session,
    source: str,
    update_tag: int,
) -> None:
    """Run cleanup for DEPENDS_ON matchlinks for a specific SBOM source."""
    cleanup_job = GraphJob.from_matchlink(
        TrivyPackageDependsOnMatchLink(),
        "SBOMSource",
        source,
        update_tag,
    )
    cleanup_job.run(neo4j_session)


@timeit
def sync_sbom_from_s3(
    neo4j_session: Session,
    sbom_s3_bucket: str,
    sbom_s3_prefix: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    boto3_session: boto3.Session,
) -> None:
    """
    Sync SBOM results from S3.

    Args:
        neo4j_session: Neo4j session for database operations.
        sbom_s3_bucket: S3 bucket containing SBOM files.
        sbom_s3_prefix: S3 prefix path containing SBOM files.
        update_tag: Update tag for tracking.
        common_job_parameters: Common job parameters for cleanup.
        boto3_session: boto3 session for S3 operations.
    """
    logger.info("Using SBOM results from s3://%s/%s", sbom_s3_bucket, sbom_s3_prefix)

    json_files = get_json_files_in_s3(sbom_s3_bucket, sbom_s3_prefix, boto3_session)

    if not json_files:
        logger.error(
            "SBOM sync was configured, but there are no JSON files in bucket "
            "'%s' with prefix '%s'. Skipping SBOM sync to avoid potential data loss.",
            sbom_s3_bucket,
            sbom_s3_prefix,
        )
        raise ValueError("No SBOM JSON files found in S3.")

    logger.debug("Processing %d SBOM files from S3", len(json_files))
    s3_client = boto3_session.client("s3")
    processed_sources: list[str] = []

    for s3_object_key in json_files:
        source = f"s3://{sbom_s3_bucket}/{s3_object_key}"
        logger.debug("Reading SBOM from S3: %s", source)

        try:
            response = s3_client.get_object(Bucket=sbom_s3_bucket, Key=s3_object_key)
            sbom_json = response["Body"].read().decode("utf-8")
            sbom_data = json.loads(sbom_json)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON from %s: %s", source, e)
            continue
        except Exception as e:
            logger.error("Failed to read %s: %s", source, e)
            continue

        sync_single_sbom(neo4j_session, sbom_data, source, update_tag)
        processed_sources.append(source)

    # Cleanup dependency matchlinks per source
    for source in processed_sources:
        cleanup_sbom_dependencies(neo4j_session, source, update_tag)


@timeit
def sync_sbom_from_dir(
    neo4j_session: Session,
    results_dir: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync SBOM results from local files.

    Args:
        neo4j_session: Neo4j session for database operations.
        results_dir: Directory containing SBOM JSON files.
        update_tag: Update tag for tracking.
        common_job_parameters: Common job parameters for cleanup.
    """
    logger.info("Using SBOM results from %s", results_dir)

    json_files = get_json_files_in_dir(results_dir)

    if not json_files:
        logger.error(
            "SBOM sync was configured, but no JSON files found in %s.",
            results_dir,
        )
        raise ValueError("No SBOM JSON files found on disk.")

    logger.debug("Processing %d local SBOM files", len(json_files))
    processed_sources: list[str] = []

    for file_path in json_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                sbom_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON from %s: %s", file_path, e)
            continue
        except Exception as e:
            logger.error("Failed to read %s: %s", file_path, e)
            continue

        sync_single_sbom(neo4j_session, sbom_data, file_path, update_tag)
        processed_sources.append(file_path)

    # Cleanup dependency matchlinks per source
    for source in processed_sources:
        cleanup_sbom_dependencies(neo4j_session, source, update_tag)


@timeit
def start_sbom_ingestion(neo4j_session: Session, config: Config) -> None:
    """
    Start SBOM ingestion from S3 or local files.

    This function enriches existing TrivyPackage nodes with dependency graph
    information from Syft CycloneDX SBOMs. It should run AFTER Trivy ingestion.

    Args:
        neo4j_session: Neo4j session for database operations.
        config: Configuration object containing S3 or directory paths.
    """
    if not config.sbom_s3_bucket and not config.sbom_results_dir:
        logger.info("SBOM configuration not provided. Skipping SBOM ingestion.")
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    if config.sbom_results_dir:
        sync_sbom_from_dir(
            neo4j_session,
            config.sbom_results_dir,
            config.update_tag,
            common_job_parameters,
        )
        return

    if config.sbom_s3_prefix is None:
        config.sbom_s3_prefix = ""

    boto3_session = boto3.Session()

    sync_sbom_from_s3(
        neo4j_session,
        config.sbom_s3_bucket,
        config.sbom_s3_prefix,
        config.update_tag,
        common_job_parameters,
        boto3_session,
    )
