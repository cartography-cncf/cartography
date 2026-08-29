import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snyk.util import attributes
from cartography.intel.snyk.util import list_jsonapi_resources
from cartography.intel.snyk.util import relationship_id
from cartography.intel.snyk.util import require_id
from cartography.models.snyk.issue import SnykIssueSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get(session: requests.Session, base_url: str, org_id: str) -> list[dict[str, Any]]:
    return list_jsonapi_resources(session, f"{base_url}/orgs/{org_id}/issues")


def _first_cve(identifiers: Any) -> str | None:
    if not isinstance(identifiers, dict):
        return None
    cves = identifiers.get("CVE") or identifiers.get("cve")
    if not isinstance(cves, list):
        return None
    for cve in cves:
        if isinstance(cve, str) and cve.startswith("CVE-"):
            return cve
    return None


def _flatten_identifiers(identifiers: Any) -> list[str]:
    if not isinstance(identifiers, dict):
        return []
    result = []
    for values in identifiers.values():
        if isinstance(values, list):
            result.extend(value for value in values if isinstance(value, str))
    return sorted(set(result))


def _scan_item_project_id(issue: dict[str, Any], attrs: dict[str, Any]) -> str | None:
    project_id = relationship_id(issue, "scan_item")
    if project_id:
        return project_id
    scan_item = attrs.get("scan_item") or attrs.get("scanItem") or {}
    if isinstance(scan_item, dict) and scan_item.get("type") == "project":
        value = scan_item.get("id")
        return value if isinstance(value, str) else None
    return None


def transform(issues: list[dict[str, Any]], org_id: str) -> list[dict[str, Any]]:
    result = []
    for issue in issues:
        attrs = attributes(issue)
        identifiers = attrs.get("identifiers") or {}
        cve_id = _first_cve(identifiers)
        result.append(
            {
                "id": require_id(issue, "issue"),
                "title": attrs.get("title"),
                "cve_id": cve_id,
                "has_cve": "true" if cve_id else "false",
                "severity": attrs.get("effective_severity_level")
                or attrs.get("severity"),
                "status": attrs.get("status"),
                "ignored": attrs.get("ignored"),
                "cvss_score": attrs.get("cvss_score"),
                "exploit_maturity": attrs.get("exploit_maturity"),
                "package_name": attrs.get("package_name"),
                "package_version": attrs.get("package_version"),
                "is_upgradable": attrs.get("is_upgradable"),
                "created_at": attrs.get("created_at"),
                "updated_at": attrs.get("updated_at"),
                "description": attrs.get("description"),
                "identifiers": _flatten_identifiers(identifiers),
                "project_id": _scan_item_project_id(issue, attrs),
                "org_id": org_id,
            }
        )
    return result


@timeit
def load_issues(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnykIssueSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SnykIssueSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    base_url: str,
    org_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    data = transform(get(session, base_url, org_id), org_id)
    load_issues(neo4j_session, data, org_id, update_tag)
