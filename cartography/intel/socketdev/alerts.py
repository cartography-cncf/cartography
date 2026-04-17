import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.socketdev.alert import SocketDevAlertSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)
_BASE_URL = "https://api.socket.dev/v0"
_PAGE_SIZE = 1000


@timeit
def get(api_token: str, org_slug: str) -> list[dict[str, Any]]:
    """
    Fetch all alerts for the given Socket.dev organization.
    Handles cursor-based pagination.
    """
    all_alerts: list[dict[str, Any]] = []
    cursor: str | None = None

    while True:
        params: dict[str, Any] = {
            "per_page": _PAGE_SIZE,
        }
        if cursor:
            params["startAfterCursor"] = cursor

        response = requests.get(
            f"{_BASE_URL}/orgs/{org_slug}/alerts",
            headers={
                "Authorization": f"Bearer {api_token}",
                "Accept": "application/json",
            },
            params=params,
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        items = data.get("items", [])
        all_alerts.extend(items)

        cursor = data.get("endCursor")
        if not cursor or not items:
            break

    logger.debug("Fetched %d Socket.dev alerts", len(all_alerts))
    return all_alerts


def transform(raw_alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Transform raw alert data for ingestion.
    Flattens vulnerability and location fields into the top-level dict.
    """
    alerts = []
    for alert in raw_alerts:
        # Extract vulnerability fields if present
        vuln = alert.get("vulnerability") or {}
        # Extract first location entry if present
        locations = alert.get("locations") or []
        location = locations[0] if locations else {}
        artifact = location.get("artifact") or {}

        alerts.append(
            {
                "id": alert["id"],
                "key": alert.get("key"),
                "type": alert.get("type"),
                "category": alert.get("category"),
                "severity": alert.get("severity"),
                "status": alert.get("status"),
                "title": alert.get("title"),
                "description": alert.get("description"),
                "dashboardUrl": alert.get("dashboardUrl"),
                "createdAt": alert.get("createdAt"),
                "updatedAt": alert.get("updatedAt"),
                "clearedAt": alert.get("clearedAt"),
                # Vulnerability fields
                "cve_id": vuln.get("cveId"),
                "cvss_score": vuln.get("cvssScore"),
                "epss_score": vuln.get("epssScore"),
                "epss_percentile": vuln.get("epssPercentile"),
                "is_kev": vuln.get("isKev"),
                "first_patched_version": vuln.get(
                    "firstPatchedVersionIdentifier",
                ),
                # Location fields
                "action": location.get("action"),
                "repo_slug": location.get("repoSlug"),
                "branch": location.get("branch"),
                "artifact_name": artifact.get("name"),
                "artifact_version": artifact.get("version"),
                "artifact_type": artifact.get("type"),
            },
        )
    return alerts


@timeit
def load_alerts(
    neo4j_session: neo4j.Session,
    alerts: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SocketDevAlertSchema(),
        alerts,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        SocketDevAlertSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_alerts(
    neo4j_session: neo4j.Session,
    api_token: str,
    org_slug: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Socket.dev alerts for the given organization.
    """
    logger.info("Starting Socket.dev alerts sync")
    raw_alerts = get(api_token, org_slug)
    alerts = transform(raw_alerts)
    org_id = common_job_parameters["ORG_ID"]
    load_alerts(neo4j_session, alerts, org_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed Socket.dev alerts sync")
