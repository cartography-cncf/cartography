import hashlib
import re
from collections import defaultdict
from typing import Any
from urllib.parse import urlparse

from cartography.intel.trivy.util import make_normalized_package_id

SEVERITY_MAP = {
    "0": "informational",
    "1": "low",
    "2": "medium",
    "3": "high",
    "4": "critical",
    "5": "critical",
    "info": "informational",
    "informational": "informational",
    "low": "low",
    "medium": "medium",
    "high": "high",
    "critical": "critical",
}

STATUS_MAP = {
    "open": "open",
    "active": "open",
    "new": "open",
    "accepted": "accepted",
    "risk accepted": "accepted",
    "fixed": "fixed",
    "resolved": "resolved",
    "closed": "closed",
}


def normalize_tenant_id(api_url: str) -> str:
    hostname = urlparse(api_url).hostname
    return hostname or api_url.rstrip("/")


def transform_tenant(api_url: str, tenant_id: str) -> list[dict[str, Any]]:
    return [
        {
            "id": tenant_id,
            "name": tenant_id,
            "api_url": api_url.rstrip("/"),
        },
    ]


def transform_vulnerabilities(
    rows: list[dict[str, Any]],
    tenant_id: str,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    resources: list[dict[str, Any]] = []
    images: list[dict[str, Any]] = []
    packages: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []

    for row in rows:
        resource = _entity(row, "resource", "r", "CloudResource", "KubernetesResource")
        vulnerability = _entity(row, "vulnerability", "finding", "v", "Vulnerability")
        package = _entity(row, "package", "p", "Package")

        resource_row = _resource_from_entity(resource, tenant_id)
        if resource_row:
            resources.append(resource_row)

        image_row = _image_from_entities(resource, vulnerability)
        if image_row:
            images.append(image_row)

        package_row = _package_from_entities(package, vulnerability, image_row)
        if package_row:
            packages.append(package_row)

        finding_row = _vulnerability_finding_from_entities(
            vulnerability,
            resource_row,
            package_row,
            image_row,
        )
        if finding_row:
            findings.append(finding_row)

    return (
        _dedupe(resources),
        _dedupe(images),
        _dedupe(packages),
        _dedupe(findings),
    )


def transform_security_findings(
    rows: list[dict[str, Any]],
    tenant_id: str,
    source_entity: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    resources: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []

    for row in rows:
        resource = _entity(row, "resource", "r", "CloudResource", "KubernetesResource")
        finding = _entity(row, "finding", "security_finding", "f", source_entity)
        resource_row = _resource_from_entity(resource, tenant_id)
        if resource_row:
            resources.append(resource_row)
        finding_row = _generic_finding_from_entity(
            finding,
            resource_row,
            source_entity,
            "SYSDIG-SECURITY",
        )
        if finding_row:
            findings.append(finding_row)

    return _dedupe(resources), _dedupe(findings)


def transform_risk_findings(
    rows: list[dict[str, Any]],
    tenant_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    resources: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []

    for row in rows:
        resource = _entity(row, "resource", "r", "CloudResource", "KubernetesResource")
        finding = _entity(row, "finding", "risk_finding", "f", "RiskFinding")
        resource_row = _resource_from_entity(resource, tenant_id)
        if resource_row:
            resources.append(resource_row)
        finding_row = _generic_finding_from_entity(
            finding,
            resource_row,
            "RiskFinding",
            "SYSDIG-RISK",
        )
        if finding_row:
            finding_row["definition_id"] = _first(
                finding,
                "definitionId",
                "definition_id",
                "riskId",
                "risk_id",
            )
            findings.append(finding_row)

    return _dedupe(resources), _dedupe(findings)


def transform_runtime_event_summaries(
    rows: list[dict[str, Any]],
    tenant_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    resources: list[dict[str, Any]] = []
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        resource = _entity(row, "resource", "r", "CloudResource", "KubernetesResource")
        event = _entity(row, "event", "runtime_event", "e", "RuntimeEvent")
        resource_row = _resource_from_entity(resource, tenant_id)
        if resource_row:
            resources.append(resource_row)
        resource_id = (
            resource_row["id"] if resource_row else _first(event, "resourceId")
        )
        key = (
            resource_id,
            _first(event, "ruleName", "rule_name", "rule"),
            _first(event, "policyId", "policy_id"),
            normalize_severity(_first(event, "severity", "priority")),
            _first(event, "source"),
            _first(event, "engine"),
        )
        grouped[key].append(event)

    summaries: list[dict[str, Any]] = []
    for key, events in grouped.items():
        resource_id, rule_name, policy_id, severity, source, engine = key
        if not resource_id or not rule_name:
            continue
        first_seen = min(
            filter(None, (_timestamp(event) for event in events)), default=None
        )
        last_seen = max(
            filter(None, (_timestamp(event) for event in events)), default=None
        )
        representative = events[0]
        summaries.append(
            {
                "id": stable_id("SRE", *key),
                "title": rule_name,
                "severity": severity,
                "type": "runtime_event",
                "status": "open",
                "first_seen": first_seen,
                "last_seen": last_seen,
                "event_count": len(events),
                "rule_name": rule_name,
                "rule_tags": _tags(representative),
                "policy_id": policy_id,
                "source": source,
                "engine": engine,
                "resource_id": resource_id,
                "representative_event_id": _first(
                    representative, "id", "eventId", "event_id"
                ),
                "url": _first(representative, "url", "link"),
            }
        )

    return _dedupe(resources), _dedupe(summaries)


def normalize_severity(value: Any) -> str | None:
    if value is None:
        return None
    return SEVERITY_MAP.get(str(value).strip().lower(), str(value).strip().lower())


def normalize_status(value: Any) -> str | None:
    if value is None:
        return None
    return STATUS_MAP.get(str(value).strip().lower(), str(value).strip().lower())


def normalize_digest(value: Any) -> str | None:
    if not value:
        return None
    digest = str(value).strip()
    if re.fullmatch(r"[a-fA-F0-9]{64}", digest):
        return f"sha256:{digest.lower()}"
    if digest.startswith("sha256:"):
        return digest.lower()
    return digest


def stable_id(prefix: str, *parts: Any) -> str:
    material = "|".join(str(part) for part in parts if part is not None)
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return f"{prefix}|{digest}"


def _entity(row: dict[str, Any], *names: str) -> dict[str, Any]:
    for name in names:
        value = row.get(name)
        if isinstance(value, dict):
            return value
    for value in row.values():
        if not isinstance(value, dict):
            continue
        entity_type = _first(value, "type", "entityType", "entity_type", "kind")
        if entity_type and any(
            str(entity_type).lower() == name.lower() for name in names
        ):
            return value
    return {}


def _resource_from_entity(
    resource: dict[str, Any],
    tenant_id: str,
) -> dict[str, Any] | None:
    if not resource:
        return None
    resource_id = _first(
        resource,
        "id",
        "uid",
        "resourceId",
        "resource_id",
        "arn",
        "cloudResourceId",
    )
    if not resource_id:
        resource_id = stable_id("SR", tenant_id, resource)

    return {
        "id": str(resource_id),
        "name": _first(resource, "name", "resourceName", "resource_name"),
        "type": _first(resource, "type", "kind", "resourceType", "resource_type"),
        "cloud_provider": _first(resource, "cloudProvider", "cloud_provider"),
        "cloud_account_id": _first(
            resource, "accountId", "account_id", "cloudAccountId"
        ),
        "cloud_region": _first(resource, "region", "cloudRegion", "cloud_region"),
        "cloud_resource_id": _first(
            resource, "resourceId", "resource_id", "cloudResourceId"
        ),
        "cloud_resource_arn": _first(resource, "arn", "cloudResourceArn"),
        "kubernetes_cluster": _first(resource, "cluster", "clusterName"),
        "kubernetes_namespace": _first(resource, "namespace", "namespaceName"),
        "kubernetes_workload": _first(
            resource, "workload", "workloadName", "podName", "deployment"
        ),
        "kubernetes_kind": _first(resource, "kind", "kubernetesKind"),
        "container_name": _first(resource, "containerName", "container_name"),
        "image_digest": normalize_digest(_first(resource, "imageDigest", "digest")),
        "image_uri": _first(resource, "image", "imageUri", "image_uri"),
    }


def _image_from_entities(
    resource: dict[str, Any],
    vulnerability: dict[str, Any],
) -> dict[str, Any] | None:
    digest = normalize_digest(
        _first(vulnerability, "imageDigest", "image_digest", "digest")
        or _first(resource, "imageDigest", "digest")
    )
    if not digest:
        return None
    return {
        "id": digest,
        "digest": digest,
        "uri": _first(vulnerability, "image", "imageUri", "image_uri")
        or _first(resource, "image", "imageUri", "image_uri"),
        "architecture": _first(resource, "architecture", "arch"),
        "os": _first(resource, "os", "operatingSystem"),
    }


def _package_from_entities(
    package: dict[str, Any],
    vulnerability: dict[str, Any],
    image: dict[str, Any] | None,
) -> dict[str, Any] | None:
    name = _first(package, "name", "packageName", "package_name") or _first(
        vulnerability, "packageName", "package_name"
    )
    version = _first(package, "version", "packageVersion", "package_version") or _first(
        vulnerability, "packageVersion", "package_version"
    )
    pkg_type = _first(package, "type", "packageType", "package_type") or _first(
        vulnerability, "packageType", "package_type"
    )
    purl = _first(package, "purl", "PURL") or _first(vulnerability, "purl", "PURL")
    normalized_id = make_normalized_package_id(
        purl=purl,
        name=name,
        version=version,
        pkg_type=pkg_type,
    )
    if not normalized_id:
        return None
    return {
        "id": normalized_id,
        "normalized_id": normalized_id,
        "name": name,
        "version": version,
        "type": pkg_type.lower() if isinstance(pkg_type, str) else pkg_type,
        "purl": purl,
        "image_digest": image["digest"] if image else None,
    }


def _vulnerability_finding_from_entities(
    vulnerability: dict[str, Any],
    resource: dict[str, Any] | None,
    package: dict[str, Any] | None,
    image: dict[str, Any] | None,
) -> dict[str, Any] | None:
    cve_id = _first(vulnerability, "cveId", "cve_id", "name", "id")
    if not cve_id:
        return None
    resource_id = resource["id"] if resource else _first(vulnerability, "resourceId")
    package_id = package["normalized_id"] if package else None
    image_digest = image["digest"] if image else None
    return {
        "id": stable_id("SVF", cve_id, resource_id, package_id, image_digest),
        "name": cve_id,
        "cve_id": cve_id,
        "title": _first(vulnerability, "title") or cve_id,
        "description": _first(vulnerability, "description"),
        "severity": normalize_severity(_first(vulnerability, "severity")),
        "status": normalize_status(_first(vulnerability, "status")),
        "fix_available": _first(vulnerability, "fixAvailable", "fix_available"),
        "in_use": _first(vulnerability, "inUse", "in_use"),
        "exploit_available": _first(
            vulnerability, "exploitAvailable", "exploit_available"
        ),
        "first_seen": _first(vulnerability, "firstSeen", "first_seen", "createdAt"),
        "last_seen": _first(vulnerability, "lastSeen", "last_seen", "updatedAt"),
        "resource_id": resource_id,
        "image_digest": image_digest,
        "package_normalized_id": package_id,
        "package_name": package["name"] if package else None,
        "package_version": package["version"] if package else None,
        "package_type": package["type"] if package else None,
        "url": _first(vulnerability, "url", "link"),
    }


def _generic_finding_from_entity(
    finding: dict[str, Any],
    resource: dict[str, Any] | None,
    source_entity: str,
    prefix: str,
) -> dict[str, Any] | None:
    title = _first(finding, "title", "name", "ruleName", "controlName")
    if not title:
        return None
    finding_id = _first(finding, "id", "uid", "findingId", "finding_id")
    resource_id = resource["id"] if resource else _first(finding, "resourceId")
    return {
        "id": str(finding_id) if finding_id else stable_id(prefix, title, resource_id),
        "title": title,
        "severity": normalize_severity(_first(finding, "severity")),
        "type": _first(finding, "type", "category") or source_entity,
        "status": normalize_status(_first(finding, "status", "state")),
        "first_seen": _first(finding, "firstSeen", "first_seen", "createdAt"),
        "last_seen": _first(finding, "lastSeen", "last_seen", "updatedAt"),
        "resource_id": resource_id,
        "source_entity": source_entity,
        "url": _first(finding, "url", "link"),
    }


def _first(source: dict[str, Any], *keys: str) -> Any:
    if not source:
        return None
    for key in keys:
        if key in source and source[key] not in ("", [], {}):
            return source[key]
        current: Any = source
        found = True
        for part in key.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                found = False
                break
        if found and current not in ("", [], {}):
            return current
    return None


def _timestamp(event: dict[str, Any]) -> Any:
    return _first(event, "timestamp", "time", "createdAt", "lastSeen")


def _tags(event: dict[str, Any]) -> list[str] | None:
    tags = _first(event, "ruleTags", "rule_tags", "tags")
    if isinstance(tags, list):
        return [str(tag) for tag in tags]
    if isinstance(tags, str):
        return [tag.strip() for tag in tags.split(",") if tag.strip()]
    return None


def _dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[Any, dict[str, Any]] = {}
    for row in rows:
        row_id = row.get("id")
        if row_id is not None:
            by_id[row_id] = row
    return list(by_id.values())
