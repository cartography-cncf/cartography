import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sentinelone.api import get_paginated_results
from cartography.intel.sentinelone.utils import get_application_version_id
from cartography.models.sentinelone.cve import S1CVESchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(api_url: str, api_token: str, account_id: str) -> list[dict[str, Any]]:
    """
    Fetch CVE data from SentinelOne API
    Should be simple and raise exceptions on failure
    """
    logger.info("Retrieving SentinelOne CVE data")
    cves = get_paginated_results(
        api_url=api_url,
        endpoint="/web/api/v2.1/application-management/risks",
        api_token=api_token,
        params={
            "limit": 1000,
            "accountIds": account_id,
        },
    )

    logger.info("Retrieved %d CVEs from SentinelOne", len(cves))
    return cves


def transform(cves_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Transform SentinelOne CVE data for loading into Neo4j
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
            "id": cve["id"],
            "cve_id": cve["cveId"],
            # Optional fields - use .get() with None default
            "application_version_id": app_version_id,
            "base_score": cve.get("baseScore"),
            "cvss_version": cve.get("cvssVersion"),
            "days_detected": cve.get("daysDetected"),
            "detection_date": cve.get("detectionDate"),
            "last_scan_date": cve.get("lastScanDate"),
            "last_scan_result": cve.get("lastScanResult"),
            "published_date": cve.get("publishedDate"),
            "severity": cve.get("severity"),
            "status": cve.get("status"),
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
    Load SentinelOne CVE data into Neo4j
    """
    logger.info(f"Loading {len(data)} SentinelOne CVEs into Neo4j")
    load(
        neo4j_session,
        S1CVESchema(),
        data,
        lastupdated=update_tag,
        S1_ACCOUNT_ID=account_id,  # Fixed parameter name to match model
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """Remove CVE nodes that weren't updated in this sync run"""
    logger.debug("Running S1CVEs cleanup")
    GraphJob.from_node_schema(S1CVESchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync SentinelOne CVEs following the standard pattern:
    GET -> TRANSFORM -> LOAD -> CLEANUP
    """
    logger.info("Syncing SentinelOne CVE data")

    api_url = str(common_job_parameters.get("API_URL"))
    api_token = str(common_job_parameters.get("API_TOKEN"))
    account_id = str(common_job_parameters.get("S1_ACCOUNT_ID"))
    update_tag = int(common_job_parameters.get("UPDATE_TAG", 0))

    # 1. GET - Fetch data from API
    cves = get(api_url, api_token, account_id)

    # 2. TRANSFORM - Shape data for ingestion
    transformed_cves = transform(cves)

    # 3. LOAD - Ingest to Neo4j using data model
    load_cves(neo4j_session, transformed_cves, account_id, update_tag)

    # 4. CLEANUP - Remove stale data
    cleanup(neo4j_session, common_job_parameters)
