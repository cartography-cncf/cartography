import json
import logging
import os
from typing import Any
from typing import Iterable
from typing import List

import boto3
from neo4j import Session

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.trivy.findings import TrivyImageFindingSchema
from cartography.models.trivy.fix import TrivyFixSchema
from cartography.models.trivy.image_layer import ImageLayerSchema
from cartography.models.trivy.package import TrivyPackageSchema
from cartography.stats import get_stats_client
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


def _validate_packages(package_list: list[dict]) -> list[dict]:
    """
    Validates that each package has the required fields.
    Returns only packages that have both InstalledVersion and PkgName.
    """
    validated_packages: list[dict] = []
    for pkg in package_list:
        if (
            "InstalledVersion" in pkg
            and pkg["InstalledVersion"]
            and "PkgName" in pkg
            and pkg["PkgName"]
        ):
            validated_packages.append(pkg)
        else:
            logger.warning(
                "Package object does not have required fields `InstalledVersion` or `PkgName` - skipping."
            )
    return validated_packages


def transform_scan_results(
    results: list[dict], image_digest: str
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Transform raw Trivy scan results into a format suitable for loading into Neo4j.
    Returns a tuple of (findings_list, packages_list, fixes_list).
    """
    findings_list = []
    packages_list = []
    fixes_list = []

    for scan_class in results:
        # Sometimes a scan class will have no vulns and Trivy will leave the key undefined instead of showing [].
        if "Vulnerabilities" in scan_class and scan_class["Vulnerabilities"]:
            for result in scan_class["Vulnerabilities"]:
                # Transform finding data
                finding = {
                    "id": f'TIF|{result["VulnerabilityID"]}',
                    "VulnerabilityID": result["VulnerabilityID"],
                    "cve_id": result["VulnerabilityID"],
                    "Description": result.get("Description"),
                    "LastModifiedDate": result.get("LastModifiedDate"),
                    "PrimaryURL": result.get("PrimaryURL"),
                    "PublishedDate": result.get("PublishedDate"),
                    "Severity": result["Severity"],
                    "SeveritySource": result.get("SeveritySource"),
                    "Title": result.get("Title"),
                    "nvd_v2_score": None,
                    "nvd_v2_vector": None,
                    "nvd_v3_score": None,
                    "nvd_v3_vector": None,
                    "redhat_v3_score": None,
                    "redhat_v3_vector": None,
                    "ubuntu_v3_score": None,
                    "ubuntu_v3_vector": None,
                    "Class": scan_class["Class"],
                    "Type": scan_class["Type"],
                    "ImageDigest": image_digest,  # For AFFECTS relationship
                }

                # Add CVSS scores if available
                if "CVSS" in result:
                    if "nvd" in result["CVSS"]:
                        nvd = result["CVSS"]["nvd"]
                        finding["nvd_v2_score"] = nvd.get("V2Score")
                        finding["nvd_v2_vector"] = nvd.get("V2Vector")
                        finding["nvd_v3_score"] = nvd.get("V3Score")
                        finding["nvd_v3_vector"] = nvd.get("V3Vector")
                    if "redhat" in result["CVSS"]:
                        redhat = result["CVSS"]["redhat"]
                        finding["redhat_v3_score"] = redhat.get("V3Score")
                        finding["redhat_v3_vector"] = redhat.get("V3Vector")
                    if "ubuntu" in result["CVSS"]:
                        ubuntu = result["CVSS"]["ubuntu"]
                        finding["ubuntu_v3_score"] = ubuntu.get("V3Score")
                        finding["ubuntu_v3_vector"] = ubuntu.get("V3Vector")

                findings_list.append(finding)

                # Transform package data
                package_id = f"{result['InstalledVersion']}|{result['PkgName']}"
                packages_list.append(
                    {
                        "id": package_id,
                        "InstalledVersion": result["InstalledVersion"],
                        "PkgName": result["PkgName"],
                        "Class": scan_class["Class"],
                        "Type": scan_class["Type"],
                        "ImageDigest": image_digest,  # For DEPLOYED relationship
                        "FindingId": finding["id"],  # For AFFECTS relationship
                        # If Trivy provides layer attribution for the package, capture it
                        "LayerDiffID": (
                            result.get("Layer", {}).get("DiffID")
                            if isinstance(result.get("Layer"), dict)
                            else None
                        ),
                    }
                )

                # Transform fix data if available
                if result.get("FixedVersion") is not None:
                    fixes_list.append(
                        {
                            "id": f"{result['FixedVersion']}|{result['PkgName']}",
                            "FixedVersion": result["FixedVersion"],
                            "PackageId": package_id,
                            "FindingId": finding["id"],
                        }
                    )

    # Validate packages before returning
    packages_list = _validate_packages(packages_list)
    return findings_list, packages_list, fixes_list


def _parse_trivy_data(
    trivy_data: dict, source: str
) -> tuple[str | None, list[dict], str, list[str]]:
    """
    Parse Trivy scan data and extract common fields.

    Args:
        trivy_data: Raw JSON Trivy data
        source: Source identifier for error messages (file path or S3 URI)

    Returns:
        Tuple of (artifact_name, results, image_digest, diff_ids)
    """
    # Extract artifact name if present (only for file-based)
    artifact_name = trivy_data.get("ArtifactName")

    if "Results" not in trivy_data:
        logger.error(
            f"Scan data did not contain a `Results` key for {source}. This indicates a malformed scan result."
        )
        raise ValueError(f"Missing 'Results' key in scan data for {source}")

    results = trivy_data["Results"]
    if not results:
        stat_handler.incr("image_scan_no_results_count")
        logger.info(f"No vulnerabilities found for {source}")

    if "Metadata" not in trivy_data or not trivy_data["Metadata"]:
        raise ValueError(f"Missing 'Metadata' in scan data for {source}")

    repo_digests = trivy_data["Metadata"].get("RepoDigests", [])
    if not repo_digests:
        raise ValueError(f"Missing 'RepoDigests' in scan metadata for {source}")

    repo_digest = repo_digests[0]
    if "@" not in repo_digest:
        raise ValueError(f"Invalid repo digest format in {source}: {repo_digest}")

    image_digest = repo_digest.split("@")[1]
    if not image_digest:
        raise ValueError(f"Empty image digest for {source}")

    # Extract ordered diff_ids, prefer Metadata.rootfs.diff_ids, then Metadata.DiffIDs
    diff_ids: list[str] = []
    metadata = trivy_data.get("Metadata", {})
    rootfs = metadata.get("rootfs") or metadata.get("RootFS") or {}
    # Try multiple casings/keys for compatibility
    if isinstance(rootfs, dict):
        ids = rootfs.get("diff_ids") or rootfs.get("DiffIDs")
        if isinstance(ids, list):
            diff_ids = [d for d in ids if isinstance(d, str)]
    if not diff_ids:
        ids = metadata.get("diff_ids") or metadata.get("DiffIDs")
        if isinstance(ids, list):
            diff_ids = [d for d in ids if isinstance(d, str)]

    return artifact_name, results, image_digest, diff_ids


def _pairwise(seq: List[str]) -> Iterable[tuple[str, str]]:
    return zip(seq, seq[1:])


@timeit
def _load_layers_via_model(
    neo4j_session: Session,
    image_id: str,
    diff_ids: list[str],
    update_tag: int,
) -> None:
    """
    Use ImageLayerSchema to load ImageLayer nodes, NEXT edges, and HEAD/TAIL links to ECRImage.
    Also updates ECRImage.length.
    """
    if not diff_ids:
        return
    records: list[dict[str, Any]] = []
    for i, d in enumerate(diff_ids):
        rec: dict[str, Any] = {"diff_id": d}
        if i < len(diff_ids) - 1:
            rec["next_diff_id"] = diff_ids[i + 1]
        if i == 0:
            rec["head_image_ids"] = [image_id]
        if i == len(diff_ids) - 1:
            rec["tail_image_ids"] = [image_id]
        records.append(rec)

    load(
        neo4j_session,
        ImageLayerSchema(),
        records,
        lastupdated=update_tag,
    )

    # Maintain ECRImage.length
    neo4j_session.run(
        """
        MATCH (img:ECRImage {id: $image_id})
        SET img.length = $length
        """,
        image_id=image_id,
        length=len(diff_ids),
    )


@timeit
def _attribute_packages_to_layers(
    neo4j_session: Session,
    image_id: str,
    packages_list: list[dict[str, Any]],
) -> None:
    """
    INTRODUCED_IN edges are created via TrivyPackageSchema using LayerDiffID.
    This function is retained for clarity but does nothing.
    """
    return


@timeit
def _compute_and_write_lineage(
    neo4j_session: Session,
    image_id: str,
) -> None:
    """
    Compute longest-prefix base (if any) and MERGE (child)-[:BUILT_FROM]->(base).
    """
    # Find candidate base image id
    res = neo4j_session.run(
        """
        MATCH (t:ECRImage {id: $image_id})-[:HEAD]->(h)
        MATCH path=(h)-[:NEXT*0..]->(x)
        MATCH (base:ECRImage)-[:TAIL]->(x)
        WHERE length(path) = base.length - 1 AND base.id <> $image_id
        RETURN base.id AS base_id
        ORDER BY base.length DESC
        LIMIT 1
        """,
        image_id=image_id,
    )
    record = res.single()
    if record and record.get("base_id"):
        base_id = record["base_id"]
        neo4j_session.run(
            """
            MATCH (child:ECRImage {id:$child}), (base:ECRImage {id:$base})
            MERGE (child)-[:BUILT_FROM]->(base)
            """,
            child=image_id,
            base=base_id,
        )


@timeit
def sync_single_image(
    neo4j_session: Session,
    trivy_data: dict,
    source: str,
    update_tag: int,
) -> None:
    """
    Sync a single image's Trivy scan results to Neo4j.

    Args:
        neo4j_session: Neo4j session for database operations
        trivy_data: Raw Trivy JSON data
        source: Source identifier for logging (file path or image URI)
        update_tag: Update tag for tracking
    """
    try:
        _, results, image_digest, diff_ids = _parse_trivy_data(trivy_data, source)

        # Transform all data in one pass
        findings_list, packages_list, fixes_list = transform_scan_results(
            results,
            image_digest,
        )

        num_findings = len(findings_list)
        stat_handler.incr("image_scan_cve_count", num_findings)

        # Load the transformed data
        load_scan_vulns(neo4j_session, findings_list, update_tag=update_tag)
        load_scan_packages(neo4j_session, packages_list, update_tag=update_tag)
        load_scan_fixes(neo4j_session, fixes_list, update_tag=update_tag)

        # Persist layer graph, image HEAD/TAIL and length via model; derive lineage
        if diff_ids:
            _load_layers_via_model(neo4j_session, image_digest, diff_ids, update_tag)
            _compute_and_write_lineage(neo4j_session, image_digest)
        stat_handler.incr("images_processed_count")

    except Exception as e:
        logger.error(f"Failed to process scan results for {source}: {e}")
        raise


@timeit
def get_json_files_in_s3(
    s3_bucket: str, s3_prefix: str, boto3_session: boto3.Session
) -> set[str]:
    """
    List S3 objects in the S3 prefix.

    Args:
        s3_bucket: S3 bucket name containing scan results
        s3_prefix: S3 prefix path containing scan results
        boto3_session: boto3 session for dependency injection

    Returns:
        Set of S3 object keys for JSON files in the S3 prefix
    """
    s3_client = boto3_session.client("s3")

    try:
        # List objects in the S3 prefix
        paginator = s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=s3_bucket, Prefix=s3_prefix)
        results = set()

        for page in page_iterator:
            if "Contents" not in page:
                continue

            for obj in page["Contents"]:
                object_key = obj["Key"]

                # Skip non-JSON files
                if not object_key.endswith(".json"):
                    continue

                # Skip files that don't start with our prefix
                if not object_key.startswith(s3_prefix):
                    continue

                results.add(object_key)

    except Exception as e:
        logger.error(
            f"Error listing S3 objects in bucket {s3_bucket} with prefix {s3_prefix}: {e}"
        )
        raise

    logger.info(f"Found {len(results)} json files in s3://{s3_bucket}/{s3_prefix}")
    return results


@timeit
def get_json_files_in_dir(results_dir: str) -> set[str]:
    """Return set of JSON file paths under a directory."""
    results = set()
    for root, _dirs, files in os.walk(results_dir):
        for filename in files:
            if filename.endswith(".json"):
                results.add(os.path.join(root, filename))
    logger.info(f"Found {len(results)} json files in {results_dir}")
    return results


@timeit
def cleanup(neo4j_session: Session, common_job_parameters: dict[str, Any]) -> None:
    """
    Run cleanup jobs for Trivy nodes.
    """
    logger.info("Running Trivy cleanup")
    GraphJob.from_node_schema(TrivyImageFindingSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(TrivyPackageSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(TrivyFixSchema(), common_job_parameters).run(
        neo4j_session
    )
    # Custom cleanup for ImageLayer graph: remove stale NEXT/HEAD/TAIL rels tied to layers touched this run,
    # then delete orphan layers not referenced by any image or package.
    update_tag = common_job_parameters["UPDATE_TAG"]
    # Remove stale NEXT edges among updated layers
    neo4j_session.run(
        """
        MATCH (a:ImageLayer)-[r:NEXT]->(b:ImageLayer)
        WHERE (a.lastupdated = $UPDATE_TAG OR b.lastupdated = $UPDATE_TAG)
          AND r.lastupdated <> $UPDATE_TAG
        DELETE r
        """,
        UPDATE_TAG=update_tag,
    )
    # Remove stale HEAD/TAIL edges from images to updated layers
    neo4j_session.run(
        """
        MATCH (:ECRImage)-[r:HEAD|TAIL]->(l:ImageLayer)
        WHERE l.lastupdated = $UPDATE_TAG AND r.lastupdated <> $UPDATE_TAG
        DELETE r
        """,
        UPDATE_TAG=update_tag,
    )
    # Remove orphan layers that were not updated this run and have no links
    neo4j_session.run(
        """
        MATCH (l:ImageLayer)
        WHERE l.lastupdated <> $UPDATE_TAG
          AND NOT (l)-[:NEXT]-()
          AND NOT ()-[:NEXT]->(l)
          AND NOT ()-[:HEAD]->(l)
          AND NOT ()-[:TAIL]->(l)
          AND NOT ()-[:INTRODUCED_IN]->(l)
        DETACH DELETE l
        """,
        UPDATE_TAG=update_tag,
    )


@timeit
def load_scan_vulns(
    neo4j_session: Session,
    findings_list: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load TrivyImageFinding nodes into Neo4j.
    """
    load(
        neo4j_session,
        TrivyImageFindingSchema(),
        findings_list,
        lastupdated=update_tag,
    )


@timeit
def load_scan_packages(
    neo4j_session: Session,
    packages_list: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load TrivyPackage nodes into Neo4j.
    """
    load(
        neo4j_session,
        TrivyPackageSchema(),
        packages_list,
        lastupdated=update_tag,
    )


@timeit
def load_scan_fixes(
    neo4j_session: Session,
    fixes_list: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load TrivyFix nodes into Neo4j.
    """
    load(
        neo4j_session,
        TrivyFixSchema(),
        fixes_list,
        lastupdated=update_tag,
    )


@timeit
def sync_single_image_from_s3(
    neo4j_session: Session,
    image_uri: str,
    update_tag: int,
    s3_bucket: str,
    s3_object_key: str,
    boto3_session: boto3.Session,
) -> None:
    """
    Read Trivy scan results from S3 and sync to Neo4j.

    Args:
        neo4j_session: Neo4j session for database operations
        image_uri: ECR image URI
        update_tag: Update tag for tracking
        s3_bucket: S3 bucket containing scan results
        s3_object_key: S3 object key for this image's scan results
        boto3_session: boto3 session for S3 operations
    """
    s3_client = boto3_session.client("s3")

    logger.debug(f"Reading scan results from S3: s3://{s3_bucket}/{s3_object_key}")
    response = s3_client.get_object(Bucket=s3_bucket, Key=s3_object_key)
    scan_data_json = response["Body"].read().decode("utf-8")

    trivy_data = json.loads(scan_data_json)
    sync_single_image(neo4j_session, trivy_data, image_uri, update_tag)


@timeit
def sync_single_image_from_file(
    neo4j_session: Session,
    file_path: str,
    update_tag: int,
) -> None:
    """Read a Trivy JSON file from disk and sync to Neo4j."""
    logger.debug(f"Reading scan results from file: {file_path}")
    with open(file_path, encoding="utf-8") as f:
        trivy_data = json.load(f)

    sync_single_image(neo4j_session, trivy_data, file_path, update_tag)
