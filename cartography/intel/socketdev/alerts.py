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


def _flatten_field(value: Any) -> Any:
    """
    Flatten a field that may be a nested dict with a 'name' key.
    The Socket.dev API sometimes returns objects like {"name": "main", "type": null}
    where a plain string is expected. Extract the name if so.
    """
    if isinstance(value, dict):
        return value.get("name")
    return value


def transform(raw_alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Transform raw alert data for ingestion.
    Flattens vulnerability, location, repository, and artifact fields
    from the nested API response into a flat dict.
    """
    alerts = []
    for alert in raw_alerts:
        # Extract vulnerability fields if present
        vuln = alert.get("vulnerability") or {}
        # Extract first location entry if present
        locations = alert.get("locations") or []
        location = locations[0] if locations else {}
        # Repository is a nested object inside location
        repo = location.get("repository") or {}
        artifact = location.get("artifact") or {}

        # Resolve GHSA IDs — cveId is often null, ghsaIds has the identifier
        ghsa_ids = vuln.get("ghsaIds") or []
        cve_id = vuln.get("cveId")
        ghsa_id = ghsa_ids[0] if ghsa_ids else None

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
                "cve_id": cve_id,
                "ghsa_id": ghsa_id,
                "cvss_score": vuln.get("cvssScore"),
                "epss_score": vuln.get("epssScore"),
                "epss_percentile": vuln.get("epssPercentile"),
                "is_kev": vuln.get("isKev"),
                "first_patched_version": _flatten_field(
                    vuln.get("firstPatchedVersionIdentifier"),
                ),
                # Location fields
                "action": location.get("action"),
                "repo_slug": repo.get("slug"),
                "repo_fullname": repo.get("fullName"),
                "branch": _flatten_field(location.get("branch")),
                "artifact_name": _flatten_field(artifact.get("name")),
                "artifact_version": _flatten_field(artifact.get("version")),
                "artifact_type": _flatten_field(artifact.get("type")),
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
) -> list[dict[str, Any]]:
    """
    Sync Socket.dev alerts for the given organization.
    Returns the transformed alerts list for downstream use (e.g. fixes sync).
    """
    logger.info("Starting Socket.dev alerts sync")
    raw_alerts = get(api_token, org_slug)
    alerts = transform(raw_alerts)
    org_id = common_job_parameters["ORG_ID"]
    load_alerts(neo4j_session, alerts, org_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed Socket.dev alerts sync")
    return alerts
