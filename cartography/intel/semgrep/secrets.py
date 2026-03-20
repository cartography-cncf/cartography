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
            logger.info("Processed page %d of Semgrep Secrets findings.", page)
        all_findings.extend(findings)
        retries = 0
        page += 1
        if has_more:
            request_data["cursor"] = data.get("cursor")

    logger.info(
        f"Retrieved {len(all_findings)} Semgrep Secrets findings in {page} pages."
    )
    return all_findings


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
        secret_finding["repositoryUrl"] = repository.get("url")
        visibility = repository.get("visibility")
        secret_finding["repositoryVisibility"] = (
            visibility.replace("REPOSITORY_VISIBILITY_", "") if visibility else None
        )
        scm_type = repository.get("scmType")
        secret_finding["repositoryScmType"] = (
            scm_type.replace("SCM_TYPE_", "") if scm_type else None
        )
        secret_finding["ref"] = finding.get("ref")
        secret_finding["ruleHashId"] = finding.get("ruleHashId")
        severity = finding.get("severity")
        secret_finding["severity"] = (
            severity.replace("SEVERITY_", "") if severity else None
        )
        confidence = finding.get("confidence")
        secret_finding["confidence"] = (
            confidence.replace("CONFIDENCE_", "") if confidence else None
        )
        secret_finding["type"] = finding.get("type")
        validation_state = finding.get("validationState")
        secret_finding["validationState"] = (
            validation_state.replace("VALIDATION_STATE_", "")
            if validation_state
            else None
        )
        status = finding.get("status")
        secret_finding["status"] = (
            status.replace("FINDING_STATUS_", "") if status else None
        )
        secret_finding["findingPath"] = finding.get("findingPath")
        secret_finding["findingPathUrl"] = finding.get("findingPathUrl")
        secret_finding["refUrl"] = finding.get("refUrl")
        mode = finding.get("mode")
        secret_finding["mode"] = mode.replace("MODE_", "") if mode else None
        secret_finding["createdAt"] = finding.get("createdAt")
        secret_finding["updatedAt"] = finding.get("updatedAt")

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
        "Loading %d SemgrepSecretsFinding objects into the graph.",
        len(findings),
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
        raise ValueError(
            "Missing Semgrep deployment ID. Ensure that sync_deployment() has been called "
            "before sync_secrets()."
        )

    try:
        raw_secret_findings = get_secret_findings(semgrep_app_token, deployment_id)

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
    except (ReadTimeout, HTTPError) as e:
        logger.warning(
            "Semgrep Secrets sync failed, skipping Secrets for this run: %s",
            e,
            exc_info=True,
        )
