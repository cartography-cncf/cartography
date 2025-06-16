import json
import logging
from typing import Any

import boto3
from neo4j import Session

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.trivy.findings import TrivyImageFindingSchema
from cartography.models.trivy.fix import TrivyFixSchema
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
def read_scan_results_from_s3(
    boto3_session: boto3.Session,
    s3_bucket: str,
    s3_object_key: str,
    image_uri: str,
) -> tuple[list[dict], str | None]:
    """
    Read and parse Trivy scan results from S3.

    Args:
        boto3_session: boto3 session for S3 operations
        s3_bucket: S3 bucket containing scan results
        s3_object_key: S3 object key for the scan results
        image_uri: ECR image URI (for logging purposes)

    Returns:
        Tuple of (list of scan result dictionaries from the "Results" key, image digest)
    """
    s3_client = boto3_session.client("s3")

    # Read JSON scan results from S3
    logger.debug(f"Reading scan results from S3: s3://{s3_bucket}/{s3_object_key}")
    response = s3_client.get_object(Bucket=s3_bucket, Key=s3_object_key)
    scan_data_json = response["Body"].read().decode("utf-8")

    # Parse JSON data
    trivy_data = json.loads(scan_data_json)

    # Extract results using the same logic as binary scanning
    if "Results" in trivy_data and trivy_data["Results"]:
        results = trivy_data["Results"]
    else:
        stat_handler.incr("image_scan_no_results_count")
        logger.warning(
            f"S3 scan data did not contain a `Results` key for URI = {image_uri}; continuing."
        )
        results = []

    image_digest = None
    if "Metadata" in trivy_data and trivy_data["Metadata"]:
        repo_digests = trivy_data["Metadata"].get("RepoDigests", [])
        if repo_digests:
            # Sample input: 000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository@sha256:88016
            # Sample output: sha256:88016
            repo_digest = repo_digests[0]
            if "@" in repo_digest:
                image_digest = repo_digest.split("@")[1]

    return results, image_digest


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
    try:
        # Read and parse scan results from S3
        results, image_digest = read_scan_results_from_s3(
            boto3_session,
            s3_bucket,
            s3_object_key,
            image_uri,
        )
        if not image_digest:
            logger.warning(f"No image digest found for {image_uri}; skipping over.")
            return

        # Transform all data in one pass using existing function
        findings_list, packages_list, fixes_list = transform_scan_results(
            results,
            image_digest,
        )

        num_findings = len(findings_list)
        stat_handler.incr("image_scan_cve_count", num_findings)

        # Load the transformed data using existing functions
        load_scan_vulns(
            neo4j_session,
            findings_list,
            update_tag=update_tag,
        )
        load_scan_packages(
            neo4j_session,
            packages_list,
            update_tag=update_tag,
        )
        load_scan_fixes(
            neo4j_session,
            fixes_list,
            update_tag=update_tag,
        )
        stat_handler.incr("images_processed_count")

    except Exception as e:
        logger.error(
            f"Failed to process S3 scan results for {image_uri} from {s3_object_key}: {e}"
        )
        raise
