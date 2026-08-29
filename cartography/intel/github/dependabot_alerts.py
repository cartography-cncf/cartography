import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.github.util import fetch_all_rest_api_pages
from cartography.intel.github.util import github_org_url
from cartography.intel.github.util import is_github_dotcom_api_url
from cartography.intel.github.util import rest_api_base_url
from cartography.models.github.dependabot_alerts import GitHubDependabotAlertSchema
from cartography.models.github.dependabot_alerts import GitHubDependabotAlertUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

DEPENDABOT_ALERTS_API_VERSION = "2026-03-10"
DEPENDABOT_ALERT_STATES = "open,fixed,dismissed,auto_dismissed"


@dataclass(frozen=True)
class DependabotAlertsFetchResult:
    alerts: list[dict[str, Any]]
    cleanup_safe: bool


@timeit
def get(
    token: str,
    api_url: str,
    organization: str,
) -> DependabotAlertsFetchResult:
    """
    Fetch all Dependabot alerts visible to the token for a GitHub organization.

    A 403/404 means either the token is missing Dependabot alert permissions or
    the feature is unavailable. Treat that as not cleanup-safe to avoid deleting
    previously ingested alert data because of an authorization/configuration issue.
    """
    base_url = rest_api_base_url(api_url)
    endpoint = f"/orgs/{quote(organization, safe='')}/dependabot/alerts"
    params: dict[str, Any] = {
        "state": DEPENDABOT_ALERT_STATES,
        "per_page": 100,
    }
    try:
        if is_github_dotcom_api_url(api_url):
            alerts = fetch_all_rest_api_pages(
                token,
                base_url,
                endpoint,
                "",
                params=params,
                raise_on_status=(403, 404),
                api_version=DEPENDABOT_ALERTS_API_VERSION,
            )
        else:
            alerts = fetch_all_rest_api_pages(
                token,
                base_url,
                endpoint,
                "",
                params=params,
                raise_on_status=(403, 404),
            )
    except requests.exceptions.HTTPError as err:
        status = err.response.status_code if err.response is not None else None
        if status in (403, 404):
            logger.warning(
                "Skipping Dependabot alerts for GitHub org %s due to HTTP %s. "
                "The token likely lacks Dependabot alerts read permission or "
                "the endpoint is unavailable.",
                organization,
                status,
            )
            return DependabotAlertsFetchResult(alerts=[], cleanup_safe=False)
        raise

    return DependabotAlertsFetchResult(alerts=alerts, cleanup_safe=True)


def _first_identifier_value(
    identifiers: list[dict[str, Any]],
    identifier_type: str,
) -> str | None:
    for identifier in identifiers:
        if identifier.get("type") == identifier_type:
            value = identifier.get("value")
            return value if isinstance(value, str) else None
    return None


def _transform_user(user: dict[str, Any] | None) -> dict[str, Any] | None:
    if not user or not user.get("html_url"):
        return None
    return {
        "html_url": user.get("html_url"),
        "login": user.get("login"),
        "site_admin": user.get("site_admin"),
        "type": user.get("type"),
    }


def _dedupe_users(users: list[dict[str, Any]]) -> list[dict[str, Any]]:
    users_by_id: dict[str, dict[str, Any]] = {}
    for user in users:
        user_id = user.get("html_url")
        if user_id:
            users_by_id[user_id] = user
    return list(users_by_id.values())


def transform(
    alerts: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """
    Transform Dependabot alert payloads into alert and lightweight user rows.
    """
    transformed_alerts: list[dict[str, Any]] = []
    transformed_users: list[dict[str, Any]] = []

    for alert in alerts:
        alert_id = alert.get("html_url") or alert.get("url")
        if not alert_id:
            logger.debug("Skipping Dependabot alert without url/html_url.")
            continue

        dependency = alert.get("dependency") or {}
        dependency_package = dependency.get("package") or {}
        advisory = alert.get("security_advisory") or {}
        vulnerability = alert.get("security_vulnerability") or {}
        first_patched_version = vulnerability.get("first_patched_version") or {}
        cvss = advisory.get("cvss") or {}
        cvss_severities = advisory.get("cvss_severities") or {}
        cvss_v3 = cvss_severities.get("cvss_v3") or {}
        cvss_v4 = cvss_severities.get("cvss_v4") or {}
        epss = advisory.get("epss") or {}
        identifiers = advisory.get("identifiers") or []
        references = advisory.get("references") or []
        repository = alert.get("repository") or {}
        dismissed_by = _transform_user(alert.get("dismissed_by"))
        assignees = [
            transformed_user
            for assignee in alert.get("assignees") or []
            if (transformed_user := _transform_user(assignee)) is not None
        ]

        if dismissed_by is not None:
            transformed_users.append(dismissed_by)
        transformed_users.extend(assignees)

        advisory_ghsa_id = advisory.get("ghsa_id") or _first_identifier_value(
            identifiers,
            "GHSA",
        )
        advisory_cve_id = advisory.get("cve_id") or _first_identifier_value(
            identifiers,
            "CVE",
        )

        transformed_alerts.append(
            {
                "id": alert_id,
                "number": alert.get("number"),
                "state": alert.get("state"),
                "url": alert.get("url"),
                "html_url": alert.get("html_url"),
                "created_at": alert.get("created_at"),
                "updated_at": alert.get("updated_at"),
                "dismissed_at": alert.get("dismissed_at"),
                "dismissed_by_user_id": (
                    dismissed_by.get("html_url") if dismissed_by else None
                ),
                "dismissed_reason": alert.get("dismissed_reason"),
                "dismissed_comment": alert.get("dismissed_comment"),
                "fixed_at": alert.get("fixed_at"),
                "assignee_user_ids": [
                    assignee["html_url"]
                    for assignee in assignees
                    if assignee.get("html_url")
                ],
                "dependency_package_ecosystem": dependency_package.get("ecosystem"),
                "dependency_package_name": dependency_package.get("name"),
                "dependency_manifest_path": dependency.get("manifest_path"),
                "dependency_scope": dependency.get("scope"),
                "vulnerable_version_range": vulnerability.get(
                    "vulnerable_version_range"
                ),
                "first_patched_version": first_patched_version.get("identifier"),
                "severity": vulnerability.get("severity") or advisory.get("severity"),
                "advisory_ghsa_id": advisory_ghsa_id,
                "advisory_cve_id": advisory_cve_id,
                "has_cve": "true" if advisory_cve_id else "false",
                "advisory_summary": advisory.get("summary"),
                "advisory_description": advisory.get("description"),
                "advisory_published_at": advisory.get("published_at"),
                "advisory_updated_at": advisory.get("updated_at"),
                "advisory_withdrawn_at": advisory.get("withdrawn_at"),
                "cvss_score": cvss.get("score"),
                "cvss_vector_string": cvss.get("vector_string"),
                "cvss_v3_score": cvss_v3.get("score"),
                "cvss_v3_vector_string": cvss_v3.get("vector_string"),
                "cvss_v4_score": cvss_v4.get("score"),
                "cvss_v4_vector_string": cvss_v4.get("vector_string"),
                "epss_percentage": epss.get("percentage"),
                "epss_percentile": epss.get("percentile"),
                "cwe_ids": [
                    cwe["cwe_id"]
                    for cwe in advisory.get("cwes") or []
                    if cwe.get("cwe_id")
                ],
                "identifiers": [
                    identifier["value"]
                    for identifier in identifiers
                    if identifier.get("value")
                ],
                "references": [
                    reference["url"] for reference in references if reference.get("url")
                ],
                "repository_url": repository.get("html_url"),
                "repository_name": repository.get("name"),
                "repository_full_name": repository.get("full_name"),
            }
        )

    return {
        "alerts": transformed_alerts,
        "users": _dedupe_users(transformed_users),
    }


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    users: list[dict[str, Any]],
    update_tag: int,
) -> None:
    if not users:
        return
    load(
        neo4j_session,
        GitHubDependabotAlertUserSchema(),
        users,
        lastupdated=update_tag,
    )


@timeit
def load_alerts(
    neo4j_session: neo4j.Session,
    alerts: list[dict[str, Any]],
    update_tag: int,
    org_url: str,
) -> None:
    if not alerts:
        return
    load(
        neo4j_session,
        GitHubDependabotAlertSchema(),
        alerts,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    org_url: str,
) -> None:
    cleanup_params = {**common_job_parameters, "org_url": org_url}
    GraphJob.from_node_schema(
        GitHubDependabotAlertSchema(),
        cleanup_params,
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    github_api_key: str,
    github_url: str,
    organization: str,
) -> None:
    logger.info("Syncing GitHub Dependabot alerts for organization: %s", organization)
    org_url = github_org_url(github_url, organization)
    update_tag = common_job_parameters["UPDATE_TAG"]

    fetch_result = get(github_api_key, github_url, organization)
    if not fetch_result.cleanup_safe:
        logger.info(
            "Skipping Dependabot alert cleanup for GitHub org %s because fetch was not cleanup-safe.",
            organization,
        )
        return

    transformed = transform(fetch_result.alerts)
    load_users(neo4j_session, transformed["users"], update_tag)
    load_alerts(neo4j_session, transformed["alerts"], update_tag, org_url)
    cleanup(neo4j_session, common_job_parameters, org_url)
