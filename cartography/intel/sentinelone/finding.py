import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sentinelone.api import build_scope_params
from cartography.intel.sentinelone.api import get_paginated_results
from cartography.intel.sentinelone.utils import get_application_version_id
from cartography.models.sentinelone.finding import S1AppFindingSchema
from cartography.models.sentinelone.vulnerability import S1VulnerabilitySchema
from cartography.util import run_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(
    api_url: str,
    api_token: str,
    account_id: str,
    site_id: str | None = None,
) -> list[dict[str, Any]]:
    logger.info("Retrieving SentinelOne AppFinding data")
    params = build_scope_params(account_id=account_id, site_id=site_id)
    params["limit"] = 1000
    cves = get_paginated_results(
        api_url=api_url,
        endpoint="/web/api/v2.1/application-management/risks",
        api_token=api_token,
        params=params,
    )

    logger.debug("Retrieved %d AppFindings from SentinelOne", len(cves))
    return cves


def transform(
    cves_list: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
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
            "vulnerability_id": _vulnerability_id(account_id, cve["cveId"]),
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


# Accounts are cleaned up separately, so a node shared across accounts would be
# deleted by the cleanup of an account that no longer reports the CVE.
def _vulnerability_id(account_id: str, cve_id: str) -> str:
    return f"S1|{account_id}|{cve_id}"


def transform_vulnerabilities(
    cves_list: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
    vulnerabilities: dict[str, dict[str, Any]] = {}
    for cve in cves_list:
        cve_id = cve["cveId"]
        vulnerabilities.setdefault(
            cve_id,
            {
                "id": _vulnerability_id(account_id, cve_id),
                "cve_id": cve_id,
                "severity": cve.get("severity"),
                "risk_score": cve.get("riskScore"),
                "remediation_level": cve.get("remediationLevel"),
                "report_confidence": cve.get("reportConfidence"),
            },
        )
    return list(vulnerabilities.values())


@timeit
def load_vulnerabilities(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        S1VulnerabilitySchema(),
        data,
        lastupdated=update_tag,
        S1_ACCOUNT_ID=account_id,
    )


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
    GraphJob.from_node_schema(S1VulnerabilitySchema(), common_job_parameters).run(
        neo4j_session
    )


# DEPRECATED: migrates graphs synced by earlier versions; will be removed in v1.0.0.
@timeit
def migrate_legacy_cve_labels(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    # Pass only what the job reads, so the API token never reaches Neo4j.
    run_analysis_job(
        "sentinelone_cve_migration.json",
        neo4j_session,
        {
            "UPDATE_TAG": common_job_parameters["UPDATE_TAG"],
            "S1_ACCOUNT_ID": common_job_parameters["S1_ACCOUNT_ID"],
        },
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    *,
    do_cleanup: bool = True,
) -> None:
    """
    Sync SentinelOne AppFindings following the standard pattern:
    GET -> TRANSFORM -> LOAD -> CLEANUP
    """
    logger.info("Syncing SentinelOne AppFinding data")

    api_url = common_job_parameters["API_URL"]
    api_token = common_job_parameters["API_TOKEN"]
    account_id = common_job_parameters["S1_ACCOUNT_ID"]
    site_id = common_job_parameters.get("S1_SITE_ID")
    update_tag = common_job_parameters["UPDATE_TAG"]

    cves = get(api_url, api_token, account_id, site_id)
    # Findings link to their vulnerability on load, so it must exist first.
    load_vulnerabilities(
        neo4j_session,
        transform_vulnerabilities(cves, account_id),
        account_id,
        update_tag,
    )
    transformed_cves = transform(cves, account_id)
    load_cves(neo4j_session, transformed_cves, account_id, update_tag)
    if do_cleanup:
        cleanup(neo4j_session, common_job_parameters)
        migrate_legacy_cve_labels(neo4j_session, common_job_parameters)
