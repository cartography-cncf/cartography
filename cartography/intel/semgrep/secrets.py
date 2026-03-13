import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import requests
from requests.exceptions import HTTPError
from requests.exceptions import ReadTimeout

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.semgrep.findings import load_semgrep_finding_assistants
from cartography.models.semgrep.secrets import SemgrepSecretsFindingSchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)
_PAGE_SIZE = 500
_TIMEOUT = (60, 60)
_MAX_RETRIES = 3


@timeit
def get_secret_findings(
    semgrep_app_token: str, deployment_id: str
) -> List[Dict[str, Any]]:
    """
    Gets the Secrets findings associated with the passed Semgrep App token and deployment id.
    param: semgrep_app_token: The Semgrep App token to use for authentication.
    param: deployment_id: The Semgrep deployment ID to use for retrieving Secrets findings.
    """
    all_findings = []
    findings_url = f"https://semgrep.dev/api/v1/deployments/{deployment_id}/secrets"
    has_more = True
    page = 0
    retries = 0
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {semgrep_app_token}",
    }

    request_data: dict[str, Any] = {
        "limit": _PAGE_SIZE,
    }
    logger.info(
        f"Retrieving Semgrep Secrets findings for deployment '{deployment_id}'."
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
                f"Failed to retrieve Semgrep Secrets findings for page {page}. Retrying...",
            )
            retries += 1
            if retries >= _MAX_RETRIES:
                raise
            continue
        findings = data.get("findings", [])
        has_more = bool(data.get("cursor"))
        if page % 10 == 0:
            logger.info(f"Processed page {page} of Semgrep Secrets findings.")
        all_findings.extend(findings)
        retries = 0
        page += 1
        if has_more:
            request_data["cursor"] = data.get("cursor")

    logger.info(
        f"Retrieved {len(all_findings)} Semgrep Secrets findings in {page} pages."
    )
    return all_findings


def _extract_secrets_assistants(
    raw_findings: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Extracts assistant data from raw secrets findings into a flat list of dicts
    suitable for loading as SemgrepFindingAssistant nodes. Findings without an autotriage
    field are skipped.
    """
    assistants = []
    for finding in raw_findings:
        autotriage = finding.get("autotriage")
        if not autotriage:
            continue
        node: Dict[str, Any] = {"id": f"semgrep-assistant-{finding['id']}"}
        node["autotriagedVerdict"] = autotriage.get("verdict")
        node["autotriagedReason"] = autotriage.get("reason")
        # Other assistant fields are not provided by the secrets API
        node["autofixFixCode"] = None
        node["componentTag"] = None
        node["componentRisk"] = None
        node["guidanceSummary"] = None
        node["guidanceInstructions"] = None
        node["ruleExplanationSummary"] = None
        node["ruleExplanation"] = None
        assistants.append(node)
    return assistants


def transform_secret_findings(
    raw_findings: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Transforms the raw Secrets findings response from Semgrep API into a list of dicts
    that can be used to create the SemgrepSecretsFinding nodes.
    """
    findings = []
    for finding in raw_findings:
        secret_finding: Dict[str, Any] = {}
        secret_finding["id"] = finding["id"]
        repository = finding.get("repository", {})
        secret_finding["repositoryName"] = repository.get("name")
        secret_finding["repositoryVisibility"] = repository.get(
            "visibility", ""
        ).replace("REPOSITORY_VISIBILITY_", "")
        secret_finding["branch"] = finding.get("ref")
        secret_finding["ruleHashId"] = finding.get("ruleHashId")
        secret_finding["severity"] = finding.get("severity", "").replace(
            "SEVERITY_", ""
        )
        secret_finding["confidence"] = finding.get("confidence", "").replace(
            "CONFIDENCE_", ""
        )
        secret_finding["secretType"] = finding.get("type")
        secret_finding["validationState"] = finding.get("validationState", "").replace(
            "VALIDATION_STATE_", ""
        )
        secret_finding["status"] = finding.get("status", "").replace(
            "FINDING_STATUS_", ""
        )
        secret_finding["findingPath"] = finding.get("findingPath")
        secret_finding["findingPathUrl"] = finding.get("findingPathUrl")
        secret_finding["refUrl"] = finding.get("refUrl")
        secret_finding["mode"] = finding.get("mode", "").replace("MODE_", "")
        secret_finding["openedAt"] = finding.get("createdAt")
        secret_finding["updatedAt"] = finding.get("updatedAt")

        historical_info = finding.get("historicalInfo", {})
        if historical_info:
            secret_finding["historicalGitCommit"] = historical_info.get("gitCommit")
        else:
            secret_finding["historicalGitCommit"] = None

        secret_finding["assistantId"] = f"semgrep-assistant-{finding['id']}"
        findings.append(secret_finding)
    return findings


@timeit
def load_semgrep_secret_findings(
    neo4j_session: neo4j.Session,
    findings: List[Dict[str, Any]],
    deployment_id: str,
    update_tag: int,
) -> None:
    logger.debug(
        f"Loading {len(findings)} SemgrepSecretsFinding objects into the graph."
    )
    load(
        neo4j_session,
        SemgrepSecretsFindingSchema(),
        findings,
        lastupdated=update_tag,
        DEPLOYMENT_ID=deployment_id,
    )


@timeit
def cleanup_secrets(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.info("Running Semgrep Secrets findings cleanup job.")
    GraphJob.from_node_schema(
        SemgrepSecretsFindingSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_secrets(
    neo4j_session: neo4j.Session,
    semgrep_app_token: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:

    deployment_id = common_job_parameters.get("DEPLOYMENT_ID")
    if not deployment_id:
        logger.warning(
            "Missing Semgrep deployment ID, ensure that sync_deployment() has been called."
            "Skipping Secrets findings sync job.",
        )
        return

    raw_secret_findings = get_secret_findings(semgrep_app_token, deployment_id)

    logger.info("Running Semgrep FindingAssistant sync job for Secrets.")
    assistants = _extract_secrets_assistants(raw_secret_findings)
    load_semgrep_finding_assistants(
        neo4j_session, assistants, deployment_id, update_tag
    )

    logger.info("Running Semgrep Secrets findings sync job.")
    secret_findings = transform_secret_findings(raw_secret_findings)
    load_semgrep_secret_findings(
        neo4j_session, secret_findings, deployment_id, update_tag
    )

    cleanup_secrets(neo4j_session, common_job_parameters)
    merge_module_sync_metadata(
        neo4j_session=neo4j_session,
        group_type="Semgrep",
        group_id=deployment_id,
        synced_type="Secrets",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
