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
from cartography.models.semgrep.assistant import SemgrepFindingAssistantSchema
from cartography.models.semgrep.findings import SemgrepSCAFindingSchema
from cartography.models.semgrep.locations import SemgrepSCALocationSchema
from cartography.models.semgrep.sast import SemgrepSASTFindingSchema
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
    logger.info("Retrieving Semgrep SCA vulns for deployment '%s'.", deployment_slug)
    while has_more:

        try:
            response = requests.get(
                sca_url,
                params=request_data,
                headers=headers,
                timeout=_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
        except (ReadTimeout, HTTPError):
            logger.warning(
                "Failed to retrieve Semgrep SCA vulns for page %d. Retrying...",
                page,
            )
            retries += 1
            if retries >= _MAX_RETRIES:
                raise
            continue
        vulns = data["findings"]
        has_more = len(vulns) > 0
        if page % 10 == 0:
            logger.info("Processed page %d of Semgrep SCA vulnerabilities.", page)
        all_vulns.extend(vulns)
        retries = 0
        page += 1
        request_data["page"] = page

    logger.debug("Retrieved %d Semgrep SCA vulns in %d pages.", len(all_vulns), page)
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
    if "CVE" in vuln:
        return f"https://nvd.nist.gov/vuln/detail/{vuln}"
    if "GHSA" in vuln:
        return f"https://github.com/advisories/{vuln}"
    if "MAL" in vuln:
        return f"https://osv.dev/vulnerability/{vuln}"
    return None


def transform_sca_vulns(
    raw_vulns: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
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
        package = vuln["found_dependency"]["package"]
        sca_vuln["id"] = vuln["id"]
        sca_vuln["repositoryName"] = repository_name
        sca_vuln["repositoryUrl"] = vuln["repository"]["url"]
        sca_vuln["branch"] = vuln["ref"]
        sca_vuln["ruleId"] = rule_id
        sca_vuln["title"] = package + ":" + vulnerability_class
        sca_vuln["description"] = vuln["rule"]["message"]
        sca_vuln["ecosystem"] = vuln["found_dependency"]["ecosystem"]
        sca_vuln["severity"] = vuln["severity"].upper()
        sca_vuln["reachability"] = vuln[
            "reachability"
        ].upper()  # Check done to determine rechabilitity
        sca_vuln["reachableIf"] = (
            vuln["reachable_condition"].upper() if vuln["reachable_condition"] else None
        )
        sca_vuln["exposureType"] = _determine_exposure(
            vuln,
        )  # Determintes if reachable or unreachable
        dependency = f"{package}|{vuln['found_dependency']['version']}"
        sca_vuln["matchedDependency"] = dependency
        dep_url = vuln["found_dependency"]["lockfile_line_url"]
        if dep_url:  # Lock file can be null, need to set
            dep_file = dep_url.split("/")[-1].split("#")[0]
            sca_vuln["dependencyFileLocation_path"] = dep_file
            sca_vuln["dependencyFileLocation_url"] = dep_url
        else:
            if sca_vuln.get("location"):
                sca_vuln["dependencyFileLocation_path"] = sca_vuln["location"][
                    "file_path"
                ]
        sca_vuln["transitivity"] = vuln["found_dependency"]["transitivity"].upper()
        if vuln.get("vulnerability_identifier"):
            vuln_id = vuln["vulnerability_identifier"].upper()
            sca_vuln["cveId"] = vuln_id
            ref_url = _build_vuln_url(vuln_id)
            sca_vuln["ref_urls"] = [ref_url] if ref_url is not None else []
        if vuln.get("fix_recommendations") and len(vuln["fix_recommendations"]) > 0:
            fix = vuln["fix_recommendations"][0]
            dep_fix = f"{fix['package']}|{fix['version']}"
            sca_vuln["closestSafeDependency"] = dep_fix
        sca_vuln["openedAt"] = vuln["created_at"]
        sca_vuln["fixStatus"] = vuln["status"]
        sca_vuln["triageStatus"] = vuln["triage_state"]
        sca_vuln["confidence"] = vuln["confidence"]
        sca_vuln["assistantId"] = f"semgrep-assistant-{vuln['id']}"
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
    logger.debug("Loading %d SemgrepSCAFinding objects into the graph.", len(vulns))
    load(
        neo4j_session,
        SemgrepSCAFindingSchema(),
        vulns,
        lastupdated=update_tag,
        DEPLOYMENT_ID=deployment_id,
    )


@timeit
def get_sast_findings(
    semgrep_app_token: str, deployment_slug: str
) -> List[Dict[str, Any]]:
    """
    Gets the SAST findings associated with the passed Semgrep App token and deployment slug.
    param: semgrep_app_token: The Semgrep App token to use for authentication.
    param: deployment_slug: The Semgrep deployment slug to use for retrieving SAST findings.
    """
    all_findings = []
    findings_url = f"https://semgrep.dev/api/v1/deployments/{deployment_slug}/findings"
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
        "issue_type": "sast",
        "ref": "_default",
        "dedup": "true",
    }
    logger.info(
        "Retrieving Semgrep SAST findings for deployment '%s'.", deployment_slug
    )
    while has_more:
        try:
            response = requests.get(
                findings_url,
                params=request_data,
                headers=headers,
                timeout=_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
        except (ReadTimeout, HTTPError):
            logger.warning(
                "Failed to retrieve Semgrep SAST findings for page %d. Retrying...",
                page,
            )
            retries += 1
            if retries >= _MAX_RETRIES:
                raise
            continue
        findings = data["findings"]
        has_more = len(findings) > 0
        if page % 10 == 0:
            logger.info("Processed page %d of Semgrep SAST findings.", page)
        all_findings.extend(findings)
        retries = 0
        page += 1
        request_data["page"] = page

    logger.info(
        "Retrieved %d Semgrep SAST findings in %d pages.", len(all_findings), page
    )
    return all_findings


def transform_sast_findings(
    raw_findings: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Transforms the raw SAST findings response from Semgrep API into a list of dicts
    that can be used to create the SemgrepSASTFinding nodes.
    """
    findings = []
    for finding in raw_findings:
        sast_finding: Dict[str, Any] = {}
        repository_name = finding["repository"]["name"]
        rule_id = finding["rule"]["name"]
        sast_finding["id"] = finding["id"]
        sast_finding["repositoryName"] = repository_name
        sast_finding["repositoryUrl"] = finding["repository"]["url"]
        sast_finding["branch"] = finding["ref"]
        sast_finding["ruleId"] = rule_id
        sast_finding["title"] = rule_id
        sast_finding["description"] = finding["rule"]["message"]
        sast_finding["severity"] = finding["severity"].upper()
        confidence = finding.get("confidence")
        sast_finding["confidence"] = confidence.upper() if confidence else None
        sast_finding["categories"] = finding.get("categories", [])
        sast_finding["cweNames"] = finding["rule"].get("cwe_names", [])
        sast_finding["owaspNames"] = finding["rule"].get("owasp_names", [])
        location = finding.get("location", {})
        if location:
            sast_finding["filePath"] = location.get("file_path")
            sast_finding["startLine"] = location.get("line")
            sast_finding["startCol"] = location.get("column")
            sast_finding["endLine"] = location.get("end_line")
            sast_finding["endCol"] = location.get("end_column")
        sast_finding["lineOfCodeUrl"] = finding.get("line_of_code_url")
        sast_finding["state"] = finding.get("state")
        sast_finding["fixStatus"] = finding.get("status")
        sast_finding["triageStatus"] = finding.get("triage_state")
        sast_finding["openedAt"] = finding.get("created_at")
        sast_finding["assistantId"] = f"semgrep-assistant-{finding['id']}"
        findings.append(sast_finding)
    return findings


@timeit
def load_semgrep_sast_findings(
    neo4j_session: neo4j.Session,
    findings: List[Dict[str, Any]],
    deployment_id: str,
    update_tag: int,
) -> None:
    logger.debug("Loading %d SemgrepSASTFinding objects into the graph.", len(findings))
    load(
        neo4j_session,
        SemgrepSASTFindingSchema(),
        findings,
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
    logger.debug("Loading %d SemgrepSCALocation objects into the graph.", len(usages))
    load(
        neo4j_session,
        SemgrepSCALocationSchema(),
        usages,
        lastupdated=update_tag,
        DEPLOYMENT_ID=deployment_id,
    )


def _extract_assistants(
    raw_findings: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Extracts assistant data from raw findings (SAST or SCA) into a flat list of dicts
    suitable for loading as SemgrepFindingAssistant nodes. Findings without an assistant
    field are skipped.
    """
    assistants = []
    for finding in raw_findings:
        assistant = finding.get("assistant")
        if not assistant:
            continue
        node: Dict[str, Any] = {"id": f"semgrep-assistant-{finding['id']}"}
        autofix = assistant.get("autofix") or {}
        autotriage = assistant.get("autotriage") or {}
        component = assistant.get("component") or {}
        guidance = assistant.get("guidance") or {}
        rule_explanation = assistant.get("rule_explanation") or {}
        node["autofixFixCode"] = autofix.get("fix_code")
        node["autotriagedVerdict"] = autotriage.get("verdict")
        node["autotriagedReason"] = autotriage.get("reason")
        node["componentTag"] = component.get("tag")
        node["componentRisk"] = component.get("risk")
        node["guidanceSummary"] = guidance.get("summary")
        node["guidanceInstructions"] = guidance.get("instructions")
        node["ruleExplanationSummary"] = rule_explanation.get("summary")
        node["ruleExplanation"] = rule_explanation.get("explanation")
        assistants.append(node)
    return assistants


@timeit
def load_semgrep_finding_assistants(
    neo4j_session: neo4j.Session,
    assistants: List[Dict[str, Any]],
    deployment_id: str,
    update_tag: int,
) -> None:
    logger.debug(
        "Loading %d SemgrepFindingAssistant objects into the graph.", len(assistants)
    )
    load(
        neo4j_session,
        SemgrepFindingAssistantSchema(),
        assistants,
        lastupdated=update_tag,
        DEPLOYMENT_ID=deployment_id,
    )


@timeit
def sync_sast_findings(
    neo4j_session: neo4j.Session,
    semgrep_app_token: str,
    deployment_id: str,
    deployment_slug: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> bool:
    """
    Fetches, transforms, and loads Semgrep SAST findings for the given deployment.
    Returns True on success, False if the API call failed.
    """
    try:
        raw_findings = get_sast_findings(semgrep_app_token, deployment_slug)
        logger.info("Running Semgrep FindingAssistant sync job (SAST).")
        load_semgrep_finding_assistants(
            neo4j_session,
            _extract_assistants(raw_findings),
            deployment_id,
            update_tag,
        )
        logger.info("Running Semgrep SAST findings sync job.")
        load_semgrep_sast_findings(
            neo4j_session,
            transform_sast_findings(raw_findings),
            deployment_id,
            update_tag,
        )
        run_scoped_analysis_job(
            "semgrep_sast_risk_analysis.json",
            neo4j_session,
            common_job_parameters,
        )
        merge_module_sync_metadata(
            neo4j_session=neo4j_session,
            group_type="Semgrep",
            group_id=deployment_id,
            synced_type="SAST",
            update_tag=update_tag,
            stat_handler=stat_handler,
        )
        logger.info("Running Semgrep SAST findings cleanup job.")
        GraphJob.from_node_schema(
            SemgrepSASTFindingSchema(),
            common_job_parameters,
        ).run(neo4j_session)
        return True
    except (ReadTimeout, HTTPError) as e:
        logger.warning(
            "Semgrep SAST sync failed, skipping SAST for this run: %s",
            e,
            exc_info=True,
        )
        return False


@timeit
def sync_sca_findings(
    neo4j_session: neo4j.Session,
    semgrep_app_token: str,
    deployment_id: str,
    deployment_slug: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> bool:
    """
    Fetches, transforms, and loads Semgrep SCA findings for the given deployment.
    Returns True on success, False if the API call failed.
    """
    try:
        raw_vulns = get_sca_vulns(semgrep_app_token, deployment_slug)
        logger.info("Running Semgrep FindingAssistant sync job (SCA).")
        load_semgrep_finding_assistants(
            neo4j_session,
            _extract_assistants(raw_vulns),
            deployment_id,
            update_tag,
        )
        logger.info("Running Semgrep SCA findings sync job.")
        vulns, usages = transform_sca_vulns(raw_vulns)
        load_semgrep_sca_vulns(neo4j_session, vulns, deployment_id, update_tag)
        load_semgrep_sca_usages(neo4j_session, usages, deployment_id, update_tag)
        run_scoped_analysis_job(
            "semgrep_sca_risk_analysis.json",
            neo4j_session,
            common_job_parameters,
        )
        merge_module_sync_metadata(
            neo4j_session=neo4j_session,
            group_type="Semgrep",
            group_id=deployment_id,
            synced_type="SCA",
            update_tag=update_tag,
            stat_handler=stat_handler,
        )
        logger.info("Running Semgrep SCA findings cleanup job.")
        GraphJob.from_node_schema(
            SemgrepSCAFindingSchema(),
            common_job_parameters,
        ).run(neo4j_session)
        logger.info("Running Semgrep SCA Locations cleanup job.")
        GraphJob.from_node_schema(
            SemgrepSCALocationSchema(),
            common_job_parameters,
        ).run(neo4j_session)
        return True
    except (ReadTimeout, HTTPError) as e:
        logger.warning(
            "Semgrep SCA sync failed, skipping SCA for this run: %s",
            e,
            exc_info=True,
        )
        return False


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
            "Missing Semgrep deployment ID or slug, ensure that sync_deployment() has been called. "
            "Skipping findings sync job.",
        )
        return

    sast_succeeded = sync_sast_findings(
        neo4j_session,
        semgrep_app_token,
        deployment_id,
        deployment_slug,
        update_tag,
        common_job_parameters,
    )
    sca_succeeded = sync_sca_findings(
        neo4j_session,
        semgrep_app_token,
        deployment_id,
        deployment_slug,
        update_tag,
        common_job_parameters,
    )

    # Assistant cleanup runs after both pipelines so we don't prematurely
    # remove assistants belonging to the other finding type.
    if sast_succeeded or sca_succeeded:
        logger.info("Running Semgrep FindingAssistant cleanup job.")
        GraphJob.from_node_schema(
            SemgrepFindingAssistantSchema(),
            common_job_parameters,
        ).run(neo4j_session)
