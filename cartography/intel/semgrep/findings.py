import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import neo4j
import requests
from requests.exceptions import HTTPError
from requests.exceptions import ReadTimeout

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.semgrep.findings import SemgrepSCAFindingSchema
from cartography.models.semgrep.locations import SemgrepSCALocationSchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import run_scoped_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)
_PAGE_SIZE = 500
_TIMEOUT = (60, 60)
_MAX_RETRIES = 3


@timeit
def get_sca_vulns(semgrep_app_token: str, deployment_slug: str) -> List[Dict[str, Any]]:
    """
    Gets the SCA vulns associated with the passed Semgrep App token and deployment id.
    param: semgrep_app_token: The Semgrep App token to use for authentication.
    param: deployment_slug: The Semgrep deployment slug to use for retrieving SCA vulns.
    """
    all_vulns = []
    sca_url = f"https://semgrep.dev/api/v1/deployments/{deployment_slug}/findings"
    has_more = True
    page = 0
    retries = 0
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {semgrep_app_token}",
    }

    request_data: dict[str, Any] = {
        "page": page,
        "page_size": _PAGE_SIZE,
        "issue_type": "sca",
        "exposures": "reachable,always_reachable,conditionally_reachable,unreachable,unknown",
        "ref": "_default",
        "dedup": "true",
    }
    logger.info(f"Retrieving Semgrep SCA vulns for deployment '{deployment_slug}'.")
    while has_more:

        try:
            response = requests.get(sca_url, params=request_data, headers=headers, timeout=_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except (ReadTimeout, HTTPError):
            logger.warning(f"Failed to retrieve Semgrep SCA vulns for page {page}. Retrying...")
            retries += 1
            if retries >= _MAX_RETRIES:
                raise
            continue
        vulns = data["findings"]
        has_more = len(vulns) > 0
        if page % 10 == 0:
            logger.info(f"Processed page {page} of Semgrep SCA vulnerabilities.")
        all_vulns.extend(vulns)
        retries = 0
        page += 1
        request_data["page"] = page

    logger.info(f"Retrieved {len(all_vulns)} Semgrep SCA vulns in {page} pages.")
    return all_vulns


def _get_vuln_class(vuln: Dict) -> str:
    vulnerability_classes = vuln["rule"].get("vulnerability_classes", [])
    if vulnerability_classes:
        return vulnerability_classes[0]
    return "Other"


def _determine_exposure(vuln: Dict[str, Any]) -> str | None:
    # See Semgrep reachability types:
    # https://semgrep.dev/docs/semgrep-supply-chain/overview#types-of-semgrep-supply-chain-findings
    reachability_types = {
        "NO REACHABILITY ANALYSIS": 2,
        "UNREACHABLE": 2,
        "REACHABLE": 0,
        "ALWAYS REACHABLE": 0,
        "CONDITIONALLY REACHABLE": 1,
    }
    reachable_flag = vuln["reachability"]
    if reachable_flag and reachable_flag.upper() in reachability_types:
        reach_score = reachability_types[reachable_flag.upper()]
        if reach_score < reachability_types["UNREACHABLE"]:
            return "REACHABLE"
        else:
            return "UNREACHABLE"
    return None


def _build_vuln_url(vuln: str) -> str | None:
    if 'CVE' in vuln:
        return f"https://nvd.nist.gov/vuln/detail/{vuln}"
    if 'GHSA' in vuln:
        return f"https://github.com/advisories/{vuln}"
    return None


def transform_sca_vulns(raw_vulns: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """
    Transforms the raw SCA vulns response from Semgrep API into a list of dicts
    that can be used to create the SemgrepSCAFinding nodes.
    """
    vulns = []
    usages = []
    for vuln in raw_vulns:
        sca_vuln: Dict[str, Any] = {}
        # Mandatory fields
        repository_name = vuln["repository"]["name"]
        rule_id = vuln["rule"]["name"]
        vulnerability_class = _get_vuln_class(vuln)
        package = vuln['found_dependency']['package']
        sca_vuln["id"] = vuln["id"]
        sca_vuln["repositoryName"] = repository_name
        sca_vuln["branch"] = vuln["ref"]
        sca_vuln["ruleId"] = rule_id
        sca_vuln["title"] = package + ":" + vulnerability_class
        sca_vuln["description"] = vuln["rule"]["message"]
        sca_vuln["ecosystem"] = vuln["found_dependency"]["ecosystem"]
        sca_vuln["severity"] = vuln["severity"].upper()
        sca_vuln["reachability"] = vuln["reachability"].upper()  # Check done to determine rechabilitity
        sca_vuln["reachableIf"] = vuln["reachable_condition"].upper() if vuln["reachable_condition"] else None
        sca_vuln["exposureType"] = _determine_exposure(vuln)  # Determintes if reachable or unreachable
        dependency = f"{package}|{vuln['found_dependency']['version']}"
        sca_vuln["matchedDependency"] = dependency
        dep_url = vuln["found_dependency"]["lockfile_line_url"]
        if dep_url:  # Lock file can be null, need to set
            dep_file = dep_url.split("/")[-1].split("#")[0]
            sca_vuln["dependencyFileLocation_path"] = dep_file
            sca_vuln["dependencyFileLocation_url"] = dep_url
        else:
            if sca_vuln.get("location"):
                sca_vuln["dependencyFileLocation_path"] = sca_vuln["location"]["file_path"]
        sca_vuln["transitivity"] = vuln["found_dependency"]["transitivity"].upper()
        if vuln.get("vulnerability_identifier"):
            vuln_id = vuln["vulnerability_identifier"].upper()
            sca_vuln["cveId"] = vuln_id
            sca_vuln["ref_urls"] = [_build_vuln_url(vuln_id)]
        if vuln.get('fix_recommendations') and len(vuln['fix_recommendations']) > 0:
            fix = vuln['fix_recommendations'][0]
            dep_fix = f"{fix['package']}|{fix['version']}"
            sca_vuln["closestSafeDependency"] = dep_fix
        sca_vuln["openedAt"] = vuln["created_at"]
        sca_vuln["fixStatus"] = vuln["status"]
        sca_vuln["triageStatus"] = vuln["triage_state"]
        sca_vuln["confidence"] = vuln["confidence"]
        usage = vuln.get("usage")
        if usage:
            usage_dict = {}
            url = usage["location"]["url"]
            usage_dict["SCA_ID"] = sca_vuln["id"]
            usage_dict["findingId"] = hash(url.split("github.com/")[-1])
            usage_dict["path"] = usage["location"]["path"]
            usage_dict["startLine"] = usage["location"]["start_line"]
            usage_dict["startCol"] = usage["location"]["start_col"]
            usage_dict["endLine"] = usage["location"]["end_line"]
            usage_dict["endCol"] = usage["location"]["end_col"]
            usage_dict["url"] = url
            usages.append(usage_dict)
        vulns.append(sca_vuln)

    return vulns, usages


@timeit
def load_semgrep_sca_vulns(
    neo4j_session: neo4j.Session,
    vulns: List[Dict[str, Any]],
    deployment_id: str,
    update_tag: int,
) -> None:
    logger.info(f"Loading {len(vulns)} SemgrepSCAFinding objects into the graph.")
    load(
        neo4j_session,
        SemgrepSCAFindingSchema(),
        vulns,
        lastupdated=update_tag,
        DEPLOYMENT_ID=deployment_id,
    )


@timeit
def load_semgrep_sca_usages(
    neo4j_session: neo4j.Session,
    usages: List[Dict[str, Any]],
    deployment_id: str,
    update_tag: int,
) -> None:
    logger.info(f"Loading {len(usages)} SemgrepSCALocation objects into the graph.")
    load(
        neo4j_session,
        SemgrepSCALocationSchema(),
        usages,
        lastupdated=update_tag,
        DEPLOYMENT_ID=deployment_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any],
) -> None:
    logger.info("Running Semgrep SCA findings cleanup job.")
    findings_cleanup_job = GraphJob.from_node_schema(
        SemgrepSCAFindingSchema(), common_job_parameters,
    )
    findings_cleanup_job.run(neo4j_session)
    logger.info("Running Semgrep SCA Locations cleanup job.")
    locations_cleanup_job = GraphJob.from_node_schema(
        SemgrepSCALocationSchema(), common_job_parameters,
    )
    locations_cleanup_job.run(neo4j_session)


@timeit
def sync_findings(
    neo4j_session: neo4j.Session,
    semgrep_app_token: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:

    deployment_id = common_job_parameters.get("DEPLOYMENT_ID")
    deployment_slug = common_job_parameters.get("DEPLOYMENT_SLUG")
    if not deployment_id or not deployment_slug:
        logger.warning(
            "Missing Semgrep deployment ID or slug, ensure that sync_deployment() has been called."
            "Skipping SCA findings sync job.",
        )
        return

    logger.info("Running Semgrep SCA findings sync job.")
    raw_vulns = get_sca_vulns(semgrep_app_token, deployment_slug)
    vulns, usages = transform_sca_vulns(raw_vulns)
    load_semgrep_sca_vulns(neo4j_session, vulns, deployment_id, update_tag)
    load_semgrep_sca_usages(neo4j_session, usages, deployment_id, update_tag)
    run_scoped_analysis_job('semgrep_sca_risk_analysis.json', neo4j_session, common_job_parameters)

    cleanup(neo4j_session, common_job_parameters)
    merge_module_sync_metadata(
        neo4j_session=neo4j_session,
        group_type='Semgrep',
        group_id=deployment_id,
        synced_type='SCA',
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
