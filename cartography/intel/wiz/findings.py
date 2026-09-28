import logging
from time import monotonic
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.wiz.api import get_paginated
from cartography.intel.wiz.util import epoch_days_ago_iso
from cartography.intel.wiz.util import extract_cve_id
from cartography.intel.wiz.util import filter_by_project_ids
from cartography.intel.wiz.util import project_ids
from cartography.intel.wiz.util import project_names
from cartography.models.wiz.findings import WizFindingSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

FINDING_TYPE_VULNERABILITY = "VULNERABILITY"
FINDING_TYPE_CONFIGURATION = "CONFIGURATION"
FINDING_TYPE_DETECTION = "DETECTION"
_FINDING_TYPE_KEY = "_wiz_finding_type"

_VULNERABILITY_QUERY = """
query WizVulnerabilityFindings($filterBy: VulnerabilityFindingFilters, $first: Int, $after: String, $orderBy: VulnerabilityFindingOrder) {
  vulnerabilityFindings(filterBy: $filterBy, first: $first, after: $after, orderBy: $orderBy) {
    nodes {
      id
      portalUrl
      name
      CVEDescription
      CVSSSeverity
      score
      exploitabilityScore
      impactScore
      hasExploit
      hasCisaKevExploit
      status
      vendorSeverity
      firstDetectedAt
      lastDetectedAt
      resolvedAt
      description
      remediation
      detailedName
      version
      fixedVersion
      detectionMethod
      link
      locationPath
      resolutionReason
      vulnerableAsset {
        ... on VulnerableAssetBase {
          id
          type
          name
          region
          providerUniqueId
          cloudPlatform
          status
          subscriptionName
          subscriptionExternalId
          subscriptionId
        }
        ... on VulnerableAssetContainerImage {
          imageId
        }
        ... on VulnerableAssetContainer {
          ImageExternalId
          VmExternalId
        }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""

_CONFIGURATION_QUERY = """
query WizConfigurationFindings($filterBy: ConfigurationFindingFilters, $first: Int, $after: String, $orderBy: ConfigurationFindingOrder) {
  configurationFindings(filterBy: $filterBy, first: $first, after: $after, orderBy: $orderBy) {
    nodes {
      id
      targetExternalId
      targetObjectProviderUniqueId
      firstSeenAt
      updatedAt
      severity
      result
      status
      remediation
      resource {
        id
        providerId
        name
        nativeType
        type
        region
        subscription {
          id
          name
          externalId
          cloudProvider
        }
        projects {
          id
          name
        }
      }
      rule {
        id
        graphId
        name
        description
        remediationInstructions
        functionAsControl
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""

_DETECTION_QUERY = """
query WizDetections($filterBy: DetectionFilters, $first: Int, $after: String, $orderBy: DetectionOrder) {
  detections(filterBy: $filterBy, first: $first, after: $after, orderBy: $orderBy) {
    nodes {
      id
      type
      origins
      severity
      description
      createdAt
      updatedAt
      actors { id name externalId providerUniqueId type }
      resources { id name externalId providerUniqueId type }
      cloudAccounts { id name externalId cloudProvider }
      cloudOrganizations { id name externalId cloudProvider }
      primaryResource { id type name externalId region }
      ruleMatch {
        rule {
          id
          name
          builtin
        }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""


@timeit
def get(
    session: requests.Session,
    graphql_url: str,
    token: str,
    since_iso: str | None = None,
    project_id_filter: list[str] | None = None,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    vulnerability_filter: dict[str, Any] = {}
    if since_iso:
        vulnerability_filter["updatedAt"] = {"after": since_iso}

    configuration_filter: dict[str, Any] = {
        "result": ["FAIL"],
        "severity": ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
        "status": (
            ["OPEN", "IN_PROGRESS", "RESOLVED", "REJECTED"]
            if since_iso
            else ["OPEN", "IN_PROGRESS"]
        ),
    }
    if since_iso:
        configuration_filter["updatedAt"] = {"after": since_iso}

    detection_filter: dict[str, Any] = {
        "severity": {
            "equals": [
                "INFORMATIONAL",
                "LOW",
                "MEDIUM",
                "HIGH",
                "CRITICAL",
            ],
        },
    }
    if since_iso:
        detection_filter["updatedAt"] = {"after": since_iso}

    for query, connection_name, filter_by, finding_type in (
        (
            _VULNERABILITY_QUERY,
            "vulnerabilityFindings",
            vulnerability_filter or None,
            FINDING_TYPE_VULNERABILITY,
        ),
        (
            _CONFIGURATION_QUERY,
            "configurationFindings",
            configuration_filter,
            FINDING_TYPE_CONFIGURATION,
        ),
        (
            _DETECTION_QUERY,
            "detections",
            detection_filter,
            FINDING_TYPE_DETECTION,
        ),
    ):
        start_time = monotonic()
        raw_findings = get_paginated(
            session,
            graphql_url,
            token,
            query,
            connection_name,
            filter_by=filter_by,
            progress_label=f"{finding_type.lower()} findings",
        )
        logger.info(
            "Fetched %d Wiz %s findings in %.2fs",
            len(raw_findings),
            finding_type.lower(),
            monotonic() - start_time,
        )
        findings.extend(
            _with_finding_type(
                filter_by_project_ids(raw_findings, project_id_filter),
                finding_type,
            ),
        )
    return findings


def _with_finding_type(
    findings: list[dict[str, Any]],
    finding_type: str,
) -> list[dict[str, Any]]:
    return [finding | {_FINDING_TYPE_KEY: finding_type} for finding in findings]


def get_finding_id(finding: dict[str, Any], tenant_id: str) -> str:
    if finding.get("id"):
        return str(finding["id"])

    finding_type = finding.get(_FINDING_TYPE_KEY, "UNKNOWN")
    resource_id = _resource_id(finding)
    finding_key = _finding_key(finding)
    location_key = _location_key(finding)
    return "|".join(
        [
            "WizFinding",
            finding_type,
            tenant_id,
            str(resource_id or "unknown-resource"),
            str(finding_key or "unknown-finding"),
            str(location_key or "unknown-location"),
        ],
    )


def transform(
    raw_findings: list[dict[str, Any]],
    tenant_id: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for finding in raw_findings:
        finding_type = finding.get(_FINDING_TYPE_KEY)
        if finding_type == FINDING_TYPE_VULNERABILITY:
            result.append(_transform_vulnerability_finding(finding, tenant_id))
        elif finding_type == FINDING_TYPE_CONFIGURATION:
            result.append(_transform_configuration_finding(finding, tenant_id))
        elif finding_type == FINDING_TYPE_DETECTION:
            result.append(_transform_detection(finding, tenant_id))
        else:
            logger.warning(
                "Skipping Wiz finding %s with unknown finding type %s",
                finding.get("id"),
                finding_type,
            )
    return result


def _transform_vulnerability_finding(
    finding: dict[str, Any],
    tenant_id: str,
) -> dict[str, Any]:
    asset = finding.get("vulnerableAsset") or {}
    projects = finding.get("projects") or asset.get("projects") or []
    cve_id = extract_cve_id(
        finding.get("name"),
        finding.get("detailedName"),
        finding.get("description"),
        finding.get("link"),
    )
    return {
        "id": get_finding_id(finding, tenant_id),
        "finding_type": FINDING_TYPE_VULNERABILITY,
        "name": finding.get("name"),
        "status": finding.get("status"),
        "severity": finding.get("CVSSSeverity") or finding.get("vendorSeverity"),
        "vendor_severity": finding.get("vendorSeverity"),
        "result": None,
        "created_at": None,
        "updated_at": None,
        "first_seen_at": None,
        "first_detected_at": finding.get("firstDetectedAt"),
        "last_detected_at": finding.get("lastDetectedAt"),
        "resolved_at": finding.get("resolvedAt"),
        "description": finding.get("description"),
        "remediation": finding.get("remediation"),
        "cve_id": cve_id,
        "has_cve": str(cve_id is not None).lower(),
        "is_security_issue": str(cve_id is None).lower(),
        "cve_description": finding.get("CVEDescription"),
        "cvss_severity": finding.get("CVSSSeverity"),
        "score": finding.get("score"),
        "exploitability_score": finding.get("exploitabilityScore"),
        "impact_score": finding.get("impactScore"),
        "has_exploit": finding.get("hasExploit"),
        "has_cisa_kev_exploit": finding.get("hasCisaKevExploit"),
        "detailed_name": finding.get("detailedName"),
        "version": finding.get("version"),
        "fixed_version": finding.get("fixedVersion"),
        "detection_method": finding.get("detectionMethod"),
        "link": finding.get("link"),
        "portal_url": finding.get("portalUrl"),
        "location_path": finding.get("locationPath"),
        "resolution_reason": finding.get("resolutionReason"),
        "target_external_id": None,
        "target_object_provider_unique_id": None,
        "rule_id": None,
        "rule_graph_id": None,
        "rule_name": None,
        "rule_description": None,
        "rule_builtin": None,
        "rule_as_control": None,
        "resource_id": asset.get("id"),
        "resource_name": asset.get("name"),
        "resource_type": asset.get("type"),
        "resource_native_type": None,
        "resource_region": asset.get("region"),
        "resource_cloud_platform": asset.get("cloudPlatform"),
        "resource_external_id": asset.get("providerUniqueId")
        or asset.get("imageId")
        or asset.get("ImageExternalId")
        or asset.get("VmExternalId"),
        "resource_status": asset.get("status"),
        "subscription_id": asset.get("subscriptionId"),
        "subscription_external_id": asset.get("subscriptionExternalId"),
        "subscription_name": asset.get("subscriptionName"),
        "cloud_account_ids": [],
        "cloud_account_names": [],
        "cloud_organization_ids": [],
        "cloud_organization_names": [],
        "actor_ids": [],
        "actor_names": [],
        "origins": [],
        "triggering_event_ids": [],
        "project_ids": project_ids(projects),
        "project_names": project_names(projects),
    }


def _transform_configuration_finding(
    finding: dict[str, Any],
    tenant_id: str,
) -> dict[str, Any]:
    resource = finding.get("resource") or {}
    subscription = resource.get("subscription") or {}
    projects = resource.get("projects") or finding.get("projects") or []
    rule = finding.get("rule") or {}
    return {
        "id": get_finding_id(finding, tenant_id),
        "finding_type": FINDING_TYPE_CONFIGURATION,
        "name": rule.get("name"),
        "status": finding.get("status"),
        "severity": finding.get("severity"),
        "vendor_severity": None,
        "result": finding.get("result"),
        "created_at": None,
        "updated_at": finding.get("updatedAt"),
        "first_seen_at": finding.get("firstSeenAt"),
        "first_detected_at": None,
        "last_detected_at": None,
        "resolved_at": None,
        "description": rule.get("description"),
        "remediation": finding.get("remediation")
        or rule.get("remediationInstructions"),
        "cve_id": None,
        "has_cve": "false",
        "is_security_issue": "true",
        "cve_description": None,
        "cvss_severity": None,
        "score": None,
        "exploitability_score": None,
        "impact_score": None,
        "has_exploit": None,
        "has_cisa_kev_exploit": None,
        "detailed_name": None,
        "version": None,
        "fixed_version": None,
        "detection_method": None,
        "link": None,
        "portal_url": None,
        "location_path": None,
        "resolution_reason": None,
        "target_external_id": finding.get("targetExternalId"),
        "target_object_provider_unique_id": finding.get(
            "targetObjectProviderUniqueId",
        ),
        "rule_id": rule.get("id"),
        "rule_graph_id": rule.get("graphId"),
        "rule_name": rule.get("name"),
        "rule_description": rule.get("description"),
        "rule_builtin": None,
        "rule_as_control": rule.get("functionAsControl"),
        "resource_id": resource.get("id"),
        "resource_name": resource.get("name"),
        "resource_type": resource.get("type"),
        "resource_native_type": resource.get("nativeType"),
        "resource_region": resource.get("region"),
        "resource_cloud_platform": subscription.get("cloudProvider"),
        "resource_external_id": finding.get("targetExternalId")
        or finding.get("targetObjectProviderUniqueId")
        or resource.get("providerId"),
        "resource_status": None,
        "subscription_id": subscription.get("id"),
        "subscription_external_id": subscription.get("externalId"),
        "subscription_name": subscription.get("name"),
        "cloud_account_ids": [],
        "cloud_account_names": [],
        "cloud_organization_ids": [],
        "cloud_organization_names": [],
        "actor_ids": [],
        "actor_names": [],
        "origins": [],
        "triggering_event_ids": [],
        "project_ids": project_ids(projects),
        "project_names": project_names(projects),
    }


def _transform_detection(
    finding: dict[str, Any],
    tenant_id: str,
) -> dict[str, Any]:
    resource = _primary_detection_resource(finding)
    rule = ((finding.get("ruleMatch") or {}).get("rule")) or {}
    cloud_accounts = finding.get("cloudAccounts") or []
    cloud_organizations = finding.get("cloudOrganizations") or []
    actors = finding.get("actors") or []
    triggering_events = (finding.get("triggeringEvents") or {}).get("nodes") or []
    return {
        "id": get_finding_id(finding, tenant_id),
        "finding_type": FINDING_TYPE_DETECTION,
        "name": rule.get("name") or finding.get("type"),
        "status": None,
        "severity": finding.get("severity"),
        "vendor_severity": None,
        "result": None,
        "created_at": finding.get("createdAt"),
        "updated_at": finding.get("updatedAt"),
        "first_seen_at": None,
        "first_detected_at": None,
        "last_detected_at": None,
        "resolved_at": None,
        "description": finding.get("description"),
        "remediation": None,
        "cve_id": None,
        "has_cve": "false",
        "is_security_issue": "true",
        "cve_description": None,
        "cvss_severity": None,
        "score": None,
        "exploitability_score": None,
        "impact_score": None,
        "has_exploit": None,
        "has_cisa_kev_exploit": None,
        "detailed_name": None,
        "version": None,
        "fixed_version": None,
        "detection_method": None,
        "link": None,
        "portal_url": None,
        "location_path": None,
        "resolution_reason": None,
        "target_external_id": None,
        "target_object_provider_unique_id": None,
        "rule_id": rule.get("id"),
        "rule_graph_id": None,
        "rule_name": rule.get("name"),
        "rule_description": None,
        "rule_builtin": rule.get("builtin"),
        "rule_as_control": None,
        "resource_id": resource.get("id"),
        "resource_name": resource.get("name"),
        "resource_type": resource.get("type"),
        "resource_native_type": None,
        "resource_region": resource.get("region"),
        "resource_cloud_platform": None,
        "resource_external_id": resource.get("externalId")
        or resource.get("providerUniqueId"),
        "resource_status": None,
        "subscription_id": None,
        "subscription_external_id": None,
        "subscription_name": None,
        "cloud_account_ids": _ids(cloud_accounts),
        "cloud_account_names": _names(cloud_accounts),
        "cloud_organization_ids": _ids(cloud_organizations),
        "cloud_organization_names": _names(cloud_organizations),
        "actor_ids": _ids(actors),
        "actor_names": _names(actors),
        "origins": [str(origin) for origin in finding.get("origins") or []],
        "triggering_event_ids": _ids(triggering_events),
        "project_ids": [],
        "project_names": [],
    }


def _resource_id(finding: dict[str, Any]) -> str | None:
    return _primary_resource(finding).get("id")


def _finding_key(finding: dict[str, Any]) -> str | None:
    rule = finding.get("rule") or ((finding.get("ruleMatch") or {}).get("rule")) or {}
    return (
        extract_cve_id(
            finding.get("name"),
            finding.get("detailedName"),
            finding.get("description"),
            finding.get("link"),
        )
        or rule.get("id")
        or rule.get("name")
        or finding.get("type")
        or finding.get("targetExternalId")
    )


def _location_key(finding: dict[str, Any]) -> str | None:
    return (
        finding.get("version")
        or finding.get("locationPath")
        or finding.get("targetObjectProviderUniqueId")
        or finding.get("targetExternalId")
    )


def _primary_resource(finding: dict[str, Any]) -> dict[str, Any]:
    if finding.get("vulnerableAsset"):
        return finding["vulnerableAsset"]
    if finding.get("resource"):
        return finding["resource"]
    return _primary_detection_resource(finding)


def _primary_detection_resource(finding: dict[str, Any]) -> dict[str, Any]:
    primary = finding.get("primaryResource")
    if isinstance(primary, dict) and primary:
        return primary
    resources = finding.get("resources") or []
    if resources and isinstance(resources[0], dict):
        return resources[0]
    return {}


def _ids(records: list[dict[str, Any]]) -> list[str]:
    return [
        str(record["id"])
        for record in records
        if isinstance(record, dict) and record.get("id")
    ]


def _names(records: list[dict[str, Any]]) -> list[str]:
    return [
        str(record["name"])
        for record in records
        if isinstance(record, dict) and record.get("name")
    ]


@timeit
def load_findings(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        WizFindingSchema(),
        data,
        lastupdated=update_tag,
        WIZ_TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(WizFindingSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    graphql_url: str,
    token: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    lookback_days: int | None,
    project_id_filter: list[str] | None = None,
    *,
    do_cleanup: bool = True,
) -> None:
    logger.info("Syncing Wiz findings for tenant %s", tenant_id)
    since_iso = (
        epoch_days_ago_iso(update_tag, lookback_days)
        if lookback_days is not None
        else None
    )
    raw_findings = get(session, graphql_url, token, since_iso, project_id_filter)
    findings = transform(raw_findings, tenant_id)
    load_findings(neo4j_session, findings, tenant_id, update_tag)
    if do_cleanup:
        cleanup(neo4j_session, common_job_parameters)
