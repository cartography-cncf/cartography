import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from urllib.error import HTTPError

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.semgrep.deployment import SemgrepDeploymentSchema
from cartography.models.semgrep.findings import SemgrepSCAFindingSchema
from cartography.models.semgrep.locations import SemgrepSCALocationSchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import run_scoped_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)
_TIMEOUT = (60, 60)
_MAX_RETRIES = 3


@timeit
def get_deployment(semgrep_app_token: str) -> Dict[str, Any]:
    """
    Gets the deployment associated with the passed Semgrep App token.
    param: semgrep_app_token: The Semgrep App token to use for authentication.
    """
    deployment = {}
    deployment_url = "https://semgrep.dev/api/v1/deployments"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {semgrep_app_token}",
    }
    response = requests.get(deployment_url, headers=headers, timeout=_TIMEOUT)
    response.raise_for_status()

    data = response.json()
    deployment["id"] = data["deployments"][0]["id"]
    deployment["name"] = data["deployments"][0]["name"]
    deployment["slug"] = data["deployments"][0]["slug"]

    return deployment


@timeit
def get_sca_vulns(semgrep_app_token: str, deployment_id: str) -> List[Dict[str, Any]]:
    """
    Gets the SCA vulns associated with the passed Semgrep App token and deployment id.
    param: semgrep_app_token: The Semgrep App token to use for authentication.
    param: deployment_id: The Semgrep deployment id to use for retrieving SCA vulns.
    """
    all_vulns = []
    sca_url = f"https://semgrep.dev/api/v1/deployments/{deployment_id}/ssc-vulns"
    has_more = True
    cursor: Dict[str, str] = {}
    page = 1
    retries = 0
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {semgrep_app_token}",
    }

    request_data = {
        "deploymentId": deployment_id,
        "pageSize": 100,
        "exposure": ["UNREACHABLE", "REACHABLE", "UNKNOWN_EXPOSURE"],
        "refs": ["_default"],
    }

    while has_more:

        if cursor:
            request_data.update({
                "cursor": {
                    "vulnOffset": cursor["vulnOffset"],
                    "issueOffset": cursor["issueOffset"],
                },
            })
        try:
            response = requests.post(sca_url, json=request_data, headers=headers, timeout=_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except HTTPError as e:
            logger.warning(f"Failed to retrieve Semgrep SCA vulns for page {page}. Retrying...")
            retries += 1
            if retries >= _MAX_RETRIES:
                raise e
            continue
        vulns = data["vulns"]
        cursor = data.get("cursor")
        has_more = data.get("hasMore", False)
        if page % 10 == 0:
            logger.info(f"Processed {page} pages of Semgrep SCA vulnerabilities so far.")
        all_vulns.extend(vulns)
        retries = 0

    return all_vulns


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
        sca_vuln["id"] = vuln["groupKey"]
        sca_vuln["repositoryName"] = vuln["repositoryName"]
        sca_vuln["ruleId"] = vuln["advisory"]["ruleId"]
        sca_vuln["title"] = vuln["advisory"]["title"]
        sca_vuln["description"] = vuln["advisory"]["description"]
        sca_vuln["ecosystem"] = vuln["advisory"]["ecosystem"]
        sca_vuln["severity"] = vuln["advisory"]["severity"]
        sca_vuln["reachability"] = vuln["advisory"]["reachability"]
        sca_vuln["reachableIf"] = vuln["advisory"]["reachableIf"]
        sca_vuln["exposureType"] = vuln["exposureType"]
        dependency = f"{vuln['matchedDependency']['name']}|{vuln['matchedDependency']['versionSpecifier']}"
        sca_vuln["matchedDependency"] = dependency
        sca_vuln["dependencyFileLocation_path"] = vuln["dependencyFileLocation"]["path"]
        sca_vuln["dependencyFileLocation_url"] = vuln["dependencyFileLocation"]["url"]
        # Optional fields
        sca_vuln["transitivity"] = vuln.get("transitivity", None)
        cves = vuln.get("advisory", {}).get("references", {}).get("cveIds")
        if len(cves) > 0:
            # Take the first CVE
            sca_vuln["cveId"] = vuln["advisory"]["references"]["cveIds"][0]
        if vuln.get('closestSafeDependency'):
            dep_fix = f"{vuln['closestSafeDependency']['name']}|{vuln['closestSafeDependency']['versionSpecifier']}"
            sca_vuln["closestSafeDependency"] = dep_fix
        if vuln["advisory"].get("references", {}).get("urls", []):
            sca_vuln["ref_urls"] = vuln["advisory"].get("references", {}).get("urls", [])
        sca_vuln["openedAt"] = vuln.get("openedAt", None)
        sca_vuln["announcedAt"] = vuln.get("announcedAt", None)
        sca_vuln["fixStatus"] = vuln["triage"]["status"]
        for usage in vuln.get("usages", []):
            usage_dict = {}
            usage_dict["SCA_ID"] = sca_vuln["id"]
            usage_dict["findingId"] = usage["findingId"]
            usage_dict["path"] = usage["location"]["path"]
            usage_dict["startLine"] = usage["location"]["startLine"]
            usage_dict["startCol"] = usage["location"]["startCol"]
            usage_dict["endLine"] = usage["location"]["endLine"]
            usage_dict["endCol"] = usage["location"]["endCol"]
            usage_dict["url"] = usage["location"]["url"]
            usages.append(usage_dict)
        vulns.append(sca_vuln)
    return vulns, usages


@timeit
def load_semgrep_deployment(
    neo4j_session: neo4j.Session, deployment: Dict[str, Any], update_tag: int,
) -> None:
    logger.info(f"Loading Semgrep deployment info {deployment} into the graph...")
    load(
        neo4j_session,
        SemgrepDeploymentSchema(),
        [deployment],
        lastupdated=update_tag,
    )


@timeit
def load_semgrep_sca_vulns(
    neo4j_session: neo4j.Session,
    vulns: List[Dict[str, Any]],
    deployment_id: str,
    update_tag: int,
) -> None:
    logger.info(f"Loading {len(vulns)} Semgrep SCA vulns info into the graph.")
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
    logger.info(f"Loading {len(usages)} Semgrep SCA usages info into the graph.")
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
def sync(
    neo4j_sesion: neo4j.Session,
    semgrep_app_token: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.info("Running Semgrep SCA findings sync job.")
    semgrep_deployment = get_deployment(semgrep_app_token)
    deployment_id = semgrep_deployment["id"]
    load_semgrep_deployment(neo4j_sesion, semgrep_deployment, update_tag)
    common_job_parameters["DEPLOYMENT_ID"] = deployment_id
    raw_vulns = get_sca_vulns(semgrep_app_token, deployment_id)
    vulns, usages = transform_sca_vulns(raw_vulns)
    load_semgrep_sca_vulns(neo4j_sesion, vulns, deployment_id, update_tag)
    load_semgrep_sca_usages(neo4j_sesion, usages, deployment_id, update_tag)
    run_scoped_analysis_job('semgrep_sca_risk_analysis.json', neo4j_sesion, common_job_parameters)
    cleanup(neo4j_sesion, common_job_parameters)
    merge_module_sync_metadata(
        neo4j_session=neo4j_sesion,
        group_type='Semgrep',
        group_id=deployment_id,
        synced_type='SCA',
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
