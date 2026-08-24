import re
from datetime import datetime
from datetime import timezone
from typing import Any

_CVE_RE = re.compile(r"\bCVE-\d{4}-\d{4,}\b", re.IGNORECASE)


def epoch_days_ago_iso(update_tag: int, lookback_days: int) -> str:
    return datetime.fromtimestamp(
        update_tag - (lookback_days * 86400),
        tz=timezone.utc,
    ).strftime("%Y-%m-%dT%H:%M:%SZ")


def project_ids(projects: Any) -> list[str]:
    return [
        str(project["id"])
        for project in projects or []
        if isinstance(project, dict) and project.get("id")
    ]


def project_names(projects: Any) -> list[str]:
    return [
        str(project["name"])
        for project in projects or []
        if isinstance(project, dict) and project.get("name")
    ]


def extract_cve_id(*values: Any) -> str | None:
    for value in values:
        if not value:
            continue
        match = _CVE_RE.search(str(value))
        if match:
            return match.group(0).upper()
    return None


def filter_by_project_ids(
    records: list[dict[str, Any]],
    allowed_project_ids: list[str] | None,
) -> list[dict[str, Any]]:
    """
    Filter records that carry project metadata and keep records that do not.

    Wiz GraphQL responses do not expose project metadata consistently across
    issue and finding types. Dropping project-less records would make a scoped
    import silently miss supported findings.
    """
    if not allowed_project_ids:
        return records

    allowed = set(allowed_project_ids)
    filtered: list[dict[str, Any]] = []
    for record in records:
        record_project_ids = set(_record_project_ids(record))
        if record_project_ids and not record_project_ids & allowed:
            continue
        filtered.append(record)
    return filtered


def _record_project_ids(record: dict[str, Any]) -> list[str]:
    projects = record.get("projects")
    if projects:
        return project_ids(projects)

    project = record.get("project")
    if isinstance(project, dict) and project.get("id"):
        return [str(project["id"])]

    resource = record.get("resource")
    if isinstance(resource, dict) and resource.get("projects"):
        return project_ids(resource["projects"])

    vulnerable_asset = record.get("vulnerableAsset")
    if isinstance(vulnerable_asset, dict) and vulnerable_asset.get("projects"):
        return project_ids(vulnerable_asset["projects"])

    return []
