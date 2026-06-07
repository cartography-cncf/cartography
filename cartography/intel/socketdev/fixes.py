import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.socketdev.fix import SocketDevFixSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)
_BASE_URL = "https://api.socket.dev/v0"


@timeit
def get(
    api_token: str,
    org_slug: str,
    repo_slug: str,
    vulnerability_ids: str,
) -> dict[str, Any]:
    """
    Fetch fixes for the given vulnerabilities in a repository.
    Returns the raw API response dict containing fixDetails.
    """
    response = requests.get(
        f"{_BASE_URL}/orgs/{org_slug}/fixes",
        headers={
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json",
        },
        params={
            "repo_slug": repo_slug,
            "vulnerability_ids": vulnerability_ids,
        },
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def _build_dependency_id(
    purl: str,
    repo_slug: str,
    dep_lookup: dict[str, str],
) -> str | None:
    """
    Try to find the matching SocketDevDependency ID for a PURL.
    The lookup is keyed by "name|version|repo_slug" to avoid cross-repo mislinks.
    """
    try:
        # Strip scheme "pkg:"
        without_scheme = purl.split(":", 1)[1] if ":" in purl else purl
        # Split type/name@version
        path_part = (
            without_scheme.split("/", 1)[1] if "/" in without_scheme else without_scheme
        )
        if "@" in path_part:
            name, version = path_part.rsplit("@", 1)
        else:
            name = path_part
            version = ""
        lookup_key = f"{name}|{version}|{repo_slug}"
        return dep_lookup.get(lookup_key)
    except (IndexError, ValueError):
        return None


def transform(
    raw_response: dict[str, Any],
    alerts_by_vuln: dict[tuple[str, str], str],
    repo_slug: str,
    dep_lookup: dict[str, str],
) -> list[dict[str, Any]]:
    """
    Transform raw fix response into a flat list of dicts for ingestion.

    Args:
        raw_response: Raw API response from the fixes endpoint.
        alerts_by_vuln: Mapping of (vulnerability_id, repo_slug) -> alert ID.
        repo_slug: Repository slug for dependency ID resolution.
        dep_lookup: Mapping of "name|version|repo_slug" -> dependency ID.
    """
    fixes = []
    fix_details = raw_response.get("fixDetails", {})

    for vuln_id, detail in fix_details.items():
        fix_type = detail.get("type", "")
        if fix_type not in ("fixFound", "partialFixFound"):
            continue

        value = detail.get("value", {})
        fix_info = value.get("fixDetails", {})
        fix_entries = fix_info.get("fixes", [])

        # Look up alert scoped to this repo to avoid cross-repo mislinks
        alert_id = alerts_by_vuln.get((vuln_id, repo_slug))

        for fix_entry in fix_entries:
            purl = fix_entry.get("purl", "")
            fixed_version = fix_entry.get("fixedVersion", "")
            update_type = fix_entry.get("updateType")
            fix_id = f"{vuln_id}|{purl}|{fixed_version}"

            dependency_id = _build_dependency_id(purl, repo_slug, dep_lookup)

            fixes.append(
                {
                    "id": fix_id,
                    "purl": purl,
                    "fixed_version": fixed_version,
                    "update_type": update_type,
                    "vulnerability_id": vuln_id,
                    "fix_type": fix_type,
                    "alert_id": alert_id,
                    "dependency_id": dependency_id,
                },
            )
    return fixes


@timeit
def load_fixes(
    neo4j_session: neo4j.Session,
    fixes: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SocketDevFixSchema(),
        fixes,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        SocketDevFixSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_fixes(
    neo4j_session: neo4j.Session,
    api_token: str,
    org_slug: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    alerts: list[dict[str, Any]],
    dependencies: list[dict[str, Any]],
) -> None:
    """
    Sync Socket.dev fixes for the given organization.

    Queries the fixes endpoint per-repo using vulnerability IDs from
    previously synced alerts, then links fixes to alerts and dependencies.

    Args:
        alerts: Transformed alert dicts (from alerts.transform()).
        dependencies: Transformed dependency dicts (from dependencies.transform()).
    """
    logger.info("Starting Socket.dev fixes sync")

    # Build lookup: (vulnerability_id, repo_slug) -> alert ID
    # Scoped by repo to avoid linking a fix to the wrong alert when the same
    # CVE/GHSA affects multiple repos.
    alerts_by_vuln: dict[tuple[str, str], str] = {}
    # Collect all repo slugs that have alerts
    repo_slugs: set[str] = set()
    for alert in alerts:
        alert_id = alert["id"]
        repo_slug_val = alert.get("repo_slug")
        if not repo_slug_val:
            continue
        repo_slugs.add(repo_slug_val)
        # Index by (vuln_id, repo_slug) for each known identifier
        cve_id = alert.get("cve_id")
        if cve_id:
            alerts_by_vuln[(cve_id, repo_slug_val)] = alert_id
        ghsa_id = alert.get("ghsa_id")
        if ghsa_id:
            alerts_by_vuln[(ghsa_id, repo_slug_val)] = alert_id
        key = alert.get("key")
        if key:
            alerts_by_vuln[(key, repo_slug_val)] = alert_id

    if not repo_slugs:
        logger.info("No alerts with repository info found, skipping fixes sync")
        return

    # Build dependency lookup: "name|version|repo_slug" -> dependency ID
    # Scoped by repo to avoid cross-linking when identical packages exist
    # across repos.
    dep_lookup: dict[str, str] = {}
    for dep in dependencies:
        repo = dep.get("repository", "")
        key = f"{dep['name']}|{dep['version']}|{repo}"
        dep_lookup[key] = dep["id"]

    all_fixes: list[dict[str, Any]] = []
    for repo_slug_val in repo_slugs:
        logger.debug(
            "Fetching fixes for repo '%s'",
            repo_slug_val,
        )
        # Use "*" to fetch fixes for all vulnerabilities in the repo
        raw_response = get(
            api_token,
            org_slug,
            repo_slug_val,
            "*",
        )

        fixes = transform(raw_response, alerts_by_vuln, repo_slug_val, dep_lookup)
        all_fixes.extend(fixes)

    if all_fixes:
        org_id = common_job_parameters["ORG_ID"]
        load_fixes(neo4j_session, all_fixes, org_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed Socket.dev fixes sync (%d fixes)", len(all_fixes))
