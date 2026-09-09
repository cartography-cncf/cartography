import logging
from typing import Any

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3.response import BaseHTTPResponse
from urllib3.util.retry import Retry

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.trivy.util import make_normalized_package_id
from cartography.intel.trivy.util import parse_purl
from cartography.models.socketdev.fix import SocketDevFixSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)
_BASE_URL = "https://api.socket.dev/v0"
_RETRY_STATUS_CODES = (408, 429, 500, 502, 503, 504)
_MAX_RETRY_AFTER_SECONDS = 8
# Keep explicit identifier queries short enough to avoid HTTP 414 responses.
_VULNERABILITY_BATCH_SIZE = 100


class _CappedRetry(Retry):
    def get_retry_after(self, response: BaseHTTPResponse) -> float | None:
        retry_after = super().get_retry_after(response)
        if retry_after is None:
            return None
        return min(retry_after, _MAX_RETRY_AFTER_SECONDS)


def _create_session(api_token: str) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json",
        },
    )
    retry_policy = _CappedRetry(
        total=3,
        connect=3,
        read=3,
        status=3,
        other=0,
        allowed_methods=["GET"],
        status_forcelist=_RETRY_STATUS_CODES,
        backoff_factor=1,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))
    return session


@timeit
def get(
    api_session: requests.Session,
    org_slug: str,
    repo_slug: str,
    vulnerability_ids: str,
) -> dict[str, Any]:
    """
    Fetch fixes for the given vulnerabilities in a repository.
    Returns the raw API response dict containing fixDetails.
    """
    response = api_session.get(
        f"{_BASE_URL}/orgs/{org_slug}/fixes",
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
    dep_lookup: dict[tuple[str, str], str],
) -> str | None:
    """
    Try to find the matching SocketDevDependency ID for a PURL.
    The lookup is scoped by normalized package ID and repository.
    """
    normalized_id = make_normalized_package_id(purl=purl)
    if not normalized_id:
        return None
    return dep_lookup.get((normalized_id, repo_slug))


def transform(
    raw_response: dict[str, Any],
    alerts_by_vuln: dict[tuple[str, str, str, str | None, str, str], str],
    repo_slug: str,
    dep_lookup: dict[tuple[str, str], str],
) -> list[dict[str, Any]]:
    """
    Transform raw fix response into a flat list of dicts for ingestion.

    Args:
        raw_response: Raw API response from the fixes endpoint.
        alerts_by_vuln: Mapping of vulnerability, repo, package type, namespace,
            name, and version to alert ID.
        repo_slug: Repository slug for dependency ID resolution.
        dep_lookup: Mapping of (normalized package ID, repo slug) -> dependency ID.
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

        for fix_entry in fix_entries:
            purl = fix_entry.get("purl", "")
            fixed_version = fix_entry.get("fixedVersion", "")
            update_type = fix_entry.get("updateType")
            fix_id = f"{vuln_id}|{purl}|{fixed_version}"

            parsed_purl = parse_purl(purl)
            alert_id = None
            if parsed_purl and parsed_purl["name"] and parsed_purl["version"]:
                alert_id = alerts_by_vuln.get(
                    (
                        vuln_id,
                        repo_slug,
                        parsed_purl["type"],
                        parsed_purl["namespace"],
                        parsed_purl["name"],
                        parsed_purl["version"],
                    ),
                )

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

    # Scope alerts by repository and full PURL identity because one vulnerability
    # can affect packages with the same name and version across ecosystems.
    alerts_by_vuln: dict[tuple[str, str, str, str | None, str, str], str] = {}
    vulnerability_ids_by_repo: dict[str, set[str]] = {}
    for alert in alerts:
        alert_id = alert["id"]
        repo_slug_val = alert.get("repo_slug")
        if not repo_slug_val:
            continue
        artifact_name = alert.get("artifact_name")
        artifact_version = alert.get("artifact_version")
        artifact_type = alert.get("artifact_type")
        artifact_namespace = alert.get("artifact_namespace")
        cve_id = alert.get("cve_id")
        if cve_id:
            if artifact_type and artifact_name and artifact_version:
                alerts_by_vuln[
                    (
                        cve_id,
                        repo_slug_val,
                        artifact_type,
                        artifact_namespace,
                        artifact_name,
                        artifact_version,
                    )
                ] = alert_id
            vulnerability_ids_by_repo.setdefault(repo_slug_val, set()).add(cve_id)
        ghsa_id = alert.get("ghsa_id")
        if ghsa_id:
            if artifact_type and artifact_name and artifact_version:
                alerts_by_vuln[
                    (
                        ghsa_id,
                        repo_slug_val,
                        artifact_type,
                        artifact_namespace,
                        artifact_name,
                        artifact_version,
                    )
                ] = alert_id
            vulnerability_ids_by_repo.setdefault(repo_slug_val, set()).add(ghsa_id)
    if not vulnerability_ids_by_repo:
        logger.info(
            "No repository alerts with CVE or GHSA identifiers found; "
            "cleaning up stale fixes",
        )
        cleanup(neo4j_session, common_job_parameters)
        return

    # Scope normalized packages by repo to avoid cross-linking identical packages.
    dep_lookup: dict[tuple[str, str], str] = {}
    for dep in dependencies:
        normalized_id = dep.get("normalized_id")
        if not normalized_id:
            continue
        repo = dep.get("repository", "")
        dep_lookup[(normalized_id, repo)] = dep["id"]

    all_fixes: list[dict[str, Any]] = []
    with _create_session(api_token) as api_session:
        for repo_slug_val in sorted(vulnerability_ids_by_repo):
            logger.debug(
                "Fetching fixes for repo '%s'",
                repo_slug_val,
            )
            sorted_ids = sorted(vulnerability_ids_by_repo[repo_slug_val])
            for offset in range(0, len(sorted_ids), _VULNERABILITY_BATCH_SIZE):
                batch = sorted_ids[offset : offset + _VULNERABILITY_BATCH_SIZE]
                raw_response = get(
                    api_session,
                    org_slug,
                    repo_slug_val,
                    ",".join(batch),
                )

                fixes = transform(
                    raw_response, alerts_by_vuln, repo_slug_val, dep_lookup
                )
                all_fixes.extend(fixes)

    if all_fixes:
        org_id = common_job_parameters["ORG_ID"]
        load_fixes(neo4j_session, all_fixes, org_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed Socket.dev fixes sync (%d fixes)", len(all_fixes))
