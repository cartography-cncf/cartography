import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sentinelone.api import get_paginated_results
from cartography.intel.sentinelone.utils import get_application_version_id
from cartography.models.sentinelone.finding import S1AppFindingSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(api_url: str, api_token: str, account_id: str) -> list[dict[str, Any]]:
    logger.info("Retrieving SentinelOne AppFinding data")
    cves = get_paginated_results(
        api_url=api_url,
        endpoint="/web/api/v2.1/application-management/risks",
        api_token=api_token,
        params={
            "limit": 1000,
            "accountIds": account_id,
        },
    )

    logger.info("Retrieved %d AppFindings from SentinelOne", len(cves))
    return cves


def transform(cves_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Transform SentinelOne AppFinding data for loading into Neo4j
    """
    transformed_cves = []
    for cve in cves_list:
        app_version_id = get_application_version_id(
            cve.get("applicationName", "unknown"),
            cve.get("applicationVendor", "unknown"),
            cve.get("applicationVersion", "unknown"),
        )
        transformed_cve = {
            # Required fields - let them fail if missing
            "id": cve["id"],  # Use API ID as the unique identifier for the node
            "cve_id": cve["cveId"],
            # Optional fields - use .get() with None default
            "application_version_id": app_version_id,
            "severity": cve.get("severity"),
            "remediation_level": cve.get("remediationLevel"),
            "risk_score": cve.get("riskScore"),
            "report_confidence": cve.get("reportConfidence"),
            # Instance properties
            "days_detected": cve.get("daysDetected"),
            "detection_date": cve.get("detectionDate"),
            "last_scan_date": cve.get("lastScanDate"),
            "last_scan_result": cve.get("lastScanResult"),
            "status": cve.get("status"),
            "mitigation_status": cve.get("mitigationStatus"),
            "mitigation_status_reason": cve.get("mitigationStatusReason"),
            "mitigation_status_changed_by": cve.get("mitigationStatusChangedBy"),
            "mitigation_status_change_time": cve.get("mitigationStatusChangeTime"),
            "marked_by": cve.get("markedBy"),
            "marked_date": cve.get("markedDate"),
            "mark_type_description": (cve.get("markType") or {}).get("description"),
            "reason": cve.get("reason"),
            "endpoint_id": cve.get("endpointId"),
        }

        transformed_cves.append(transformed_cve)

    return transformed_cves


@timeit
def load_cves(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    """
    Load SentinelOne AppFinding data into Neo4j
    """
    logger.info(f"Loading {len(data)} SentinelOne AppFindings into Neo4j")
    load(
        neo4j_session,
        S1AppFindingSchema(),
        data,
        lastupdated=update_tag,
        S1_ACCOUNT_ID=account_id,  # Fixed parameter name to match model
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """Remove AppFinding nodes that weren't updated in this sync run"""
    logger.debug("Running S1AppFinding cleanup")
    GraphJob.from_node_schema(S1AppFindingSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync SentinelOne AppFindings following the standard pattern:
    GET -> TRANSFORM -> LOAD -> CLEANUP
    """
    logger.info("Syncing SentinelOne AppFinding data")

    api_url = common_job_parameters.get("API_URL", "")
    api_token = common_job_parameters.get("API_TOKEN", "")
    account_id = common_job_parameters.get("S1_ACCOUNT_ID", "")
    update_tag = common_job_parameters.get("UPDATE_TAG", 0)

    if not api_url or not api_token or not account_id or not update_tag:
        logger.error("Missing required parameters for SentinelOne AppFinding sync")
        return

    cves = get(api_url, api_token, account_id)
    transformed_cves = transform(cves)
    load_cves(neo4j_session, transformed_cves, account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
