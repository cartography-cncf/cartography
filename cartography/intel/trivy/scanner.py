import json
import logging
import subprocess
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import neo4j
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


@timeit
def _call_trivy_binary(
    ecr_image_uri: str, trivy_path: str, image_cmd_args: Optional[List[str]] = None
) -> bytes:
    """
    Calls Trivy to scan an image and returns the output.

    Args:
        ecr_image_uri: The URI of the image to scan
        trivy_path: Path to the Trivy binary
        image_cmd_args: Optional list of command arguments

    Returns:
        bytes: The command output

    Raises:
        subprocess.CalledProcessError: If the command fails
    """
    command = [trivy_path, "--quiet", "image"]
    if image_cmd_args:
        command.extend(image_cmd_args)
    command.append(ecr_image_uri)

    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        stat_handler.incr("image_scan_success_count")
        return output
    except subprocess.CalledProcessError:
        stat_handler.incr("image_scan_fatal_count")
        raise


@timeit
def _call_trivy_update_db(trivy_path: str) -> None:
    """
    Updates the Trivy vulnerability database.

    Args:
        trivy_path: Path to the Trivy binary

    Raises:
        subprocess.CalledProcessError: If the update fails
    """
    command = [trivy_path, "--quiet", "image", "--download-db-only"]

    try:
        subprocess.check_output(command, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        logger.error(
            f"Trivy database update failed: {exc.output.decode('utf-8') if isinstance(exc.output, bytes) else exc.output}"
        )
        raise


def _build_image_subcommand(
    skip_update: bool,
    ignore_unfixed: bool = True,
    triage_filter_policy_file_path: Optional[str] = None,
    os_findings_only: bool = False,
    list_all_pkgs: bool = False,
    security_checks: Optional[str] = None,
) -> List[str]:
    """
    Builds the subcommand arguments for Trivy image scanning.

    Args:
        skip_update: Whether to skip database update
        ignore_unfixed: Whether to ignore unfixed vulnerabilities
        triage_filter_policy_file_path: Path to policy file for filtering
        os_findings_only: Whether to only scan OS vulnerabilities
        list_all_pkgs: Whether to list all packages
        security_checks: Comma-separated list of security checks to run

    Returns:
        List[str]: List of command arguments
    """
    args = [
        "--format",
        "json",
        "--timeout",
        "15m",  # Default = 5 minutes. Some images need 15 mins.
    ]

    if skip_update:
        args.append("--skip-update")

    if ignore_unfixed:
        args.append("--ignore-unfixed")

    if triage_filter_policy_file_path:
        args.extend(["--ignore-policy", triage_filter_policy_file_path])

    if os_findings_only:
        args.extend(["--vuln-type", "os"])

    if list_all_pkgs:
        args.append("--list-all-pkgs")

    if security_checks:
        args.extend(["--security-checks", security_checks])

    return args


@timeit
def get_scan_results_for_single_image(
    ecr_image_uri: str, image_subcmd_args: List[str], trivy_path: str
) -> List[Dict]:
    """
    Runs trivy scanner on the given ecr_image_uri and returns vuln data results.
    """
    # Get
    trivy_output_as_str: bytes = _call_trivy_binary(
        ecr_image_uri, trivy_path, image_subcmd_args
    )

    # Transform
    trivy_data: Dict = json.loads(trivy_output_as_str)
    # See https://github.com/aquasecurity/trivy/discussions/1050 for schema v2 shape
    if "Results" in trivy_data and trivy_data["Results"]:
        return trivy_data["Results"]
    else:
        stat_handler.incr("image_scan_no_results_count")
        logger.warning(
            f"trivy scan did not return a `results` key for URI = {ecr_image_uri}; continuing."
        )
        return []


def _validate_packages(package_list: List[Dict]) -> List[Dict]:
    """
    Validates that each package has the required fields.
    Returns only packages that have both InstalledVersion and PkgName.
    """
    validated_packages: List[Dict] = []
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
    results: List[Dict], image_digest: str
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
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
def cleanup(neo4j_session: Session, common_job_parameters: Dict[str, Any]) -> None:
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
    neo4j_session: neo4j.Session,
    findings_list: List[Dict[str, Any]],
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
    neo4j_session: neo4j.Session,
    packages_list: List[Dict[str, Any]],
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
    neo4j_session: neo4j.Session,
    fixes_list: List[Dict[str, Any]],
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
def sync_single_image(
    neo4j_session: neo4j.Session,
    image_tag: str,
    image_uri: str,
    repo_name: str,
    image_digest: str,
    update_tag: int,
    skip_db_update: bool,
    trivy_path: str,
    trivy_opa_policy_file_path: str,
) -> None:
    # Default scan configuration
    # - ignore_unfixed=True: Skip vulnerabilities without fixes
    # - os_findings_only=False: Scan both OS and library vulnerabilities
    # - list_all_pkgs=True: Include all packages in results
    # - security_checks="vuln": Focus on vulnerability scanning for better performance
    image_subcmd_args = _build_image_subcommand(
        skip_update=skip_db_update,
        ignore_unfixed=True,
        triage_filter_policy_file_path=trivy_opa_policy_file_path,
        os_findings_only=False,
        list_all_pkgs=True,
        security_checks="vuln",
    )

    results = get_scan_results_for_single_image(
        image_uri, image_subcmd_args, trivy_path
    )

    # Transform all data in one pass
    findings_list, packages_list, fixes_list = transform_scan_results(
        results,
        image_digest,
    )

    # Log the transformation results
    num_findings = len(findings_list)
    logger.info(
        "Transformed Trivy scan results: "
        f"repo_name = {repo_name}, "
        f"image_tag = {image_tag}, "
        f"num_findings = {num_findings}, "
        f"num_packages = {len(packages_list)}, "
        f"num_fixes = {len(fixes_list)}."
    )
    stat_handler.incr("image_scan_cve_count", num_findings)

    # Load the transformed data
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
