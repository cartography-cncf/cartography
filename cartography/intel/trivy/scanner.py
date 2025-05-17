import json
import logging
import subprocess
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from neo4j import Session

from cartography.graph.job import GraphJob
from cartography.stats import get_stats_client
from cartography.util import timeit


logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def _call_trivy_binary(ecr_image_uri: str, trivy_path: str, image_cmd_args: Optional[List[str]] = None) -> bytes:
    """
    Calls `trivy --quiet image $image_cmd_args $ecr_image_uri` and returns text output as raw string.
    """
    if image_cmd_args is None:
        image_cmd_args = []

    # Build the command with global args
    command: List[str] = [trivy_path, '--quiet']

    # Add the image subcommand with its own args
    command.append('image')
    command.extend(image_cmd_args)
    command.append(ecr_image_uri)

    try:
        trivy_output_as_str: bytes = subprocess.check_output(command, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        stat_handler.incr('image_scan_fatal_count')
        raise
    stat_handler.incr('image_scan_success_count')
    return trivy_output_as_str


@timeit
def _call_trivy_update_db(trivy_path: str) -> None:
    """
    Calls `trivy --quiet --download-db-only`.
    """
    command: List[str] = [trivy_path, '--quiet', 'image', '--download-db-only']

    # Run the command but discard the output. We expect none anyway since --quiet mode is on.
    try:
        subprocess.check_output(command, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        logger.error(
            f"`trivy image --download-db-only` failed. Error msg: "
            f"{exc.output.decode('utf-8') if type(exc.output) == bytes else exc.output}",
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
    image_subcmd_args: List[str] = [
        '--format', 'json',

        # Default = 5 minutes. Some images are humongous and need 15 mins.
        '--timeout', '15m',
    ]

    if skip_update:
        image_subcmd_args.append('--skip-update')

    if ignore_unfixed:
        image_subcmd_args.append('--ignore-unfixed')

    if triage_filter_policy_file_path:
        image_subcmd_args.extend(
            [
                '--ignore-policy', triage_filter_policy_file_path,
            ],
        )

    # Trivy default = '--vuln-type=os,library' - https://aquasecurity.github.io/trivy/v0.19.2/getting-started/cli/image/
    if os_findings_only:
        image_subcmd_args.extend(
            ['--vuln-type', 'os'],
        )

    if list_all_pkgs:
        image_subcmd_args.extend(
            ['--list-all-pkgs'],
        )

    if security_checks:
        image_subcmd_args.extend(
            ['--security-checks', security_checks],
        )

    return image_subcmd_args


@timeit
def get_scan_results_for_single_image(ecr_image_uri: str, image_subcmd_args: List[str], trivy_path: str) -> List[Dict]:
    """
    Runs trivy scanner on the given ecr_image_uri and returns vuln data results.
    """
    # Get
    trivy_output_as_str: bytes = _call_trivy_binary(ecr_image_uri, trivy_path, image_subcmd_args)

    # Transform
    trivy_data: Dict = json.loads(trivy_output_as_str)
    # See https://github.com/aquasecurity/trivy/discussions/1050 for schema v2 shape
    if 'Results' in trivy_data and trivy_data['Results']:
        return trivy_data['Results']
    else:
        stat_handler.incr('image_scan_no_results_count')
        logger.warning(f"trivy scan did not return a `results` key for URI = {ecr_image_uri}; continuing.")
        return []


def transform_scan_results(results: List[Dict]) -> List[Dict]:
    """
    Trivy results produce a nested dictionary, so we pull out some info
    from this to be added to TrivyImageFinding nodes
    """
    for scan_class in results:
        # Sometimes a scan class will have no vulns and Trivy will leave the key undefined instead of showing [].
        if 'Vulnerabilities' in scan_class and scan_class['Vulnerabilities']:
            parsed_vuln_results: List[Dict] = []
            for result in scan_class['Vulnerabilities']:
                # If ID, Severity, FixedVersion, or PkgName do not exist, fail loudly.
                # For all other fields, continue
                parsed_result = {
                    "NodeId": f'TIF|{result["VulnerabilityID"]}',
                    "VulnerabilityID": result["VulnerabilityID"],
                    "Description": result.get("Description"),
                    "LastModifiedDate": result.get("LastModifiedDate"),
                    "PrimaryURL": result.get("PrimaryURL"),
                    "PublishedDate": result.get("PublishedDate"),
                    "Severity": result["Severity"],
                    "SeveritySource": result.get("SeveritySource"),
                    "Title": result.get("Title"),
                    "InstalledVersion": result["InstalledVersion"],
                    "PkgName": result["PkgName"],
                    "FixedVersion": result.get("FixedVersion"),
                    "nvd_v2_score": None,
                    "nvd_v2_vector": None,
                    "nvd_v3_score": None,
                    "nvd_v3_vector": None,
                    "redhat_v3_score": None,
                    "redhat_v3_vector": None,
                    "ubuntu_v3_score": None,
                    "ubuntu_v3_vector": None,
                }

                if "CVSS" in result:
                    if "nvd" in result["CVSS"]:
                        nvd = result["CVSS"]["nvd"]
                        parsed_result["nvd_v2_score"] = nvd.get("V2Score")
                        parsed_result["nvd_v2_vector"] = nvd.get("V2Vector")
                        parsed_result["nvd_v3_score"] = nvd.get("V3Score")
                        parsed_result["nvd_v3_vector"] = nvd.get("V3Vector")
                    if "redhat" in result["CVSS"]:
                        redhat = result["CVSS"]["redhat"]
                        parsed_result["redhat_v3_score"] = redhat.get("V3Score")
                        parsed_result["redhat_v3_vector"] = redhat.get("V3Vector")
                    if "ubuntu" in result["CVSS"]:
                        redhat = result["CVSS"]["ubuntu"]
                        parsed_result["ubuntu_v3_score"] = redhat.get("V3Score")
                        parsed_result["ubuntu_v3_vector"] = redhat.get("V3Vector")

                parsed_vuln_results.append(parsed_result)

            scan_class['Vulnerabilities'] = parsed_vuln_results

    return results


@timeit
def cleanup(neo4j_session: Session, common_job_parameters: Dict[str, Any]) -> None:
    GraphJob.run_from_json_file(
        'trivy_scan_findings_cleanup.json', neo4j_session, common_job_parameters,
    )


@timeit
def load_scan_packages(
        neo4j_session: neo4j.Session,
        scan_results: List[Dict],
        ecr_image_digest: str,
        ecr_image_tag: str,
        ecr_repo_name: str,
        update_tag: int,
) -> None:
    for scan_class in scan_results:
        if 'Packages' in scan_class and scan_class['Packages']:
            validated_packages = _validate_packages(scan_class['Packages'], ecr_image_tag, ecr_repo_name)
            neo4j_session.write_transaction(
                _load_packages_in_single_class_tx,
                ecr_image_digest,
                ecr_image_tag,
                ecr_repo_name,
                validated_packages,
                scan_class['Class'],
                scan_class['Type'],
                update_tag,
            )


@timeit
def _load_scan_results_in_single_class_tx(
        tx: neo4j.Transaction,
        ecr_image_digest: str,
        ecr_image_tag: str,
        ecr_repo_name: str,
        vulns_of_single_class: List[Dict],
        trivy_class: str,
        trivy_type: str,
        update_tag: int,
) -> None:
    ingest_results = """
    MATCH (image:ECRImage{id: $ImageDigest})

    UNWIND $Findings as finding
        MERGE (t:TrivyImageFinding{id: finding.NodeId})
        ON CREATE SET t.firstseen = timestamp()
        SET t:Risk,
            t:CVE,
            t.name = finding.VulnerabilityID,
            t.cve_id = finding.VulnerabilityID,
            t.lastupdated = $UpdateTag,
            t.description = finding.Description,
            t.last_modified_date = finding.LastModifiedDate,
            t.primary_url = finding.PrimaryURL,
            t.published_date = finding.PublishedDate,
            t.severity = finding.Severity,
            t.severity_source = finding.SeveritySource,
            t.title = finding.Title,
            t.cvss_nvd_v2_score = finding.nvd_v2_score,
            t.cvss_nvd_v2_vector = finding.nvd_v2_vector,
            t.cvss_nvd_v3_score = finding.nvd_v3_score,
            t.cvss_nvd_v3_vector = finding.nvd_v3_vector,
            t.cvss_redhat_v3_score = finding.redhat_v3_score,
            t.cvss_redhat_v3_vector = finding.redhat_v3_vector,
            t.cvss_ubuntu_v3_score = finding.ubuntu_v3_score,
            t.cvss_ubuntu_v3_vector = finding.ubuntu_v3_vector,
            t.class = $Class,
            t.type = $Type

        MERGE (p:Package{id:  finding.InstalledVersion + '|' + finding.PkgName})
        ON CREATE SET p.installed_version = finding.InstalledVersion,
            p.name = finding.PkgName,
            p.firstseen = timestamp()
        SET p:TrivyPackage,
            p.lastupdated = $UpdateTag,
            p.version = finding.InstalledVersion,
            p.class = $Class,
            p.type = $Type

        MERGE (fix:TrivyFix{id: finding.FixedVersion + '|' + finding.PkgName})
        ON CREATE SET fix.firstseen = timestamp()
        SET fix:Fix,
            fix.version = finding.FixedVersion,
            fix.lastupdated = $UpdateTag

        MERGE (p)-[should:SHOULD_UPDATE_TO]->(fix)
        ON CREATE SET should.firstseen = timestamp()
        SET should.version = finding.FixedVersion,
            should.lastupdated = $UpdateTag

        MERGE (fix)-[applies:APPLIES_TO]->(t)
        ON CREATE SET applies.firstseen = timestamp()
        SET applies.lastupdated = $UpdateTag

        MERGE (p)-[r1:DEPLOYED]->(image)
        ON CREATE SET r1.firstseen = timestamp()
        SET r1.lastupdated = $UpdateTag

        MERGE (t)-[a:AFFECTS]->(p)
        ON CREATE SET a.firstseen = timestamp()
        SET a.lastupdated = $UpdateTag

        MERGE (t)-[a2:AFFECTS]->(image)
        ON CREATE SET a2.firstseen = timestamp()
        SET a2.lastupdated = $UpdateTag
    """
    num_findings = len(vulns_of_single_class)
    logger.info(
        "Ingesting Trivy scan results: "
        f"repo_name = {ecr_repo_name}, "
        f"image_tag = {ecr_image_tag}, "
        f"num_findings = {num_findings}, "
        f"class = {trivy_class}, "
        f"type = {trivy_type}, "
        f"update_tag = {update_tag}.",
    )
    stat_handler.incr('image_scan_cve_count', num_findings)
    tx.run(
        ingest_results,
        Findings=vulns_of_single_class,
        Class=trivy_class,
        Type=trivy_type,
        ImageDigest=ecr_image_digest,
        ImageTag=ecr_image_tag,
        RepoName=ecr_repo_name,
        UpdateTag=update_tag,
    )


@timeit
def load_scan_vulns(
        neo4j_session: neo4j.Session,
        scan_results: List[Dict[str, Any]],
        ecr_image_digest: str,
        ecr_image_tag: str,
        ecr_repo_name: str,
        update_tag: int,
) -> None:
    for scan_class in scan_results:
        # Sometimes a scan class will have no vulns and Trivy will leave the key undefined instead of showing [].
        if 'Vulnerabilities' in scan_class and scan_class['Vulnerabilities']:
            neo4j_session.write_transaction(
                _load_scan_results_in_single_class_tx,
                ecr_image_digest,
                ecr_image_tag,
                ecr_repo_name,
                scan_class['Vulnerabilities'],
                scan_class['Class'],
                scan_class['Type'],
                update_tag,
            )


@timeit
def _load_packages_in_single_class_tx(
        tx: neo4j.Transaction,
        ecr_image_digest: str,
        ecr_image_tag: str,
        ecr_repo_name: str,
        packages_of_single_class: List[Dict],
        trivy_class: str,
        trivy_type: str,
        update_tag: int,
) -> None:
    ingest_results = """
    MATCH (image:ECRImage{id: $ImageDigest})

    UNWIND $Packages as pkg
        MERGE (p:Package{id:  pkg.Version + '|' + pkg.Name})
        ON CREATE SET p.installed_version = pkg.Version,
            p.name = pkg.Name,
            p.firstseen = timestamp()
        SET p:TrivyPackage,
            p.lastupdated = $UpdateTag,
            p.version = pkg.Version,
            p.class = $Class,
            p.type = $Type

        MERGE (p)-[r1:DEPLOYED]->(image)
        ON CREATE SET r1.firstseen = timestamp()
        SET r1.lastupdated = $UpdateTag
    """
    num_packages = len(packages_of_single_class)
    logger.info(
        f"Ingesting Trivy package: "
        f"repo_name = {ecr_repo_name}, "
        f"image_tag = {ecr_image_tag}, "
        f"num_packages = {num_packages}, "
        f"class = {trivy_class}, "
        f"type = {trivy_type}.",
    )
    tx.run(
        ingest_results,
        Packages=packages_of_single_class,
        Class=trivy_class,
        Type=trivy_type,
        ImageDigest=ecr_image_digest,
        ImageTag=ecr_image_tag,
        RepoName=ecr_repo_name,
        UpdateTag=update_tag,
    )


def _validate_packages(package_list: List[Dict], ecr_image_tag: str, ecr_repo_name: str) -> List[Dict]:
    validated_packages: List[Dict] = []
    for pkg in package_list:
        if 'Version' in pkg and pkg['Version'] and 'Name' in pkg and pkg['Name']:
            validated_packages.append(pkg)
        else:
            logger.warning(
                f"Package object does not have a `Name` or `Value` - skipping. Please check why."
                f"ecr_image_tag = {ecr_image_tag}, "
                f"ecr_repo_name = {ecr_repo_name}.",
            )
    return validated_packages


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
    image_subcmd_args: List[str] = _build_image_subcommand(
        skip_db_update,
        ignore_unfixed=True,
        triage_filter_policy_file_path=trivy_opa_policy_file_path,
        os_findings_only=False,  # scan for both os and library vuln classes.
        list_all_pkgs=True,
        security_checks='vuln',  # trivy 0.30.1 says "If your scanning is slow, please try '--security-checks vuln'"
    )
    results: List[Dict] = get_scan_results_for_single_image(image_uri, image_subcmd_args, trivy_path)
    parsed_results: List[Dict] = transform_scan_results(results)
    load_scan_vulns(neo4j_session, parsed_results, image_digest, image_tag, repo_name, update_tag)
    load_scan_packages(neo4j_session, parsed_results, image_digest, image_tag, repo_name, update_tag)
    stat_handler.incr('images_processed_count')
