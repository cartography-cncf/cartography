import logging
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
from cartography.models.wiz.vulnerabilities import WizVulnerabilityFindingSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_QUERY = """
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
          cloudProviderURL
          cloudPlatform
          status
          subscriptionName
          subscriptionExternalId
          subscriptionId
          tags
        }
        ... on VulnerableAssetVirtualMachine {
          operatingSystem
          ipAddresses
        }
        ... on VulnerableAssetServerless {
          runtime
        }
        ... on VulnerableAssetContainerImage {
          imageId
        }
        ... on VulnerableAssetContainer {
          ImageExternalId
          VmExternalId
          ServerlessContainer
          PodNamespace
          PodName
          NodeName
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
    since_iso: str,
    project_id_filter: list[str] | None = None,
) -> list[dict[str, Any]]:
    raw = get_paginated(
        session,
        graphql_url,
        token,
        _QUERY,
        "vulnerabilityFindings",
        filter_by={"updatedAt": {"after": since_iso}},
    )
    return filter_by_project_ids(raw, project_id_filter)


def get_finding_id(finding: dict[str, Any], tenant_id: str) -> str:
    if finding.get("id"):
        return finding["id"]

    asset = finding.get("vulnerableAsset") or {}
    cve_id = extract_cve_id(
        finding.get("name"),
        finding.get("detailedName"),
        finding.get("description"),
        finding.get("link"),
    )
    return "|".join(
        [
            "WizVulnerabilityFinding",
            tenant_id,
            str(asset.get("id") or "unknown-resource"),
            str(cve_id or finding.get("name") or "unknown-vulnerability"),
            str(
                finding.get("version")
                or finding.get("locationPath")
                or "unknown-location"
            ),
        ],
    )


def transform(
    raw_findings: list[dict[str, Any]],
    tenant_id: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for finding in raw_findings:
        asset = finding.get("vulnerableAsset") or {}
        projects = finding.get("projects") or asset.get("projects") or []
        cve_id = extract_cve_id(
            finding.get("name"),
            finding.get("detailedName"),
            finding.get("description"),
            finding.get("link"),
        )
        result.append(
            {
                "id": get_finding_id(finding, tenant_id),
                "name": finding.get("name"),
                "cve_id": cve_id,
                "cve_description": finding.get("CVEDescription"),
                "cvss_severity": finding.get("CVSSSeverity"),
                "score": finding.get("score"),
                "exploitability_score": finding.get("exploitabilityScore"),
                "impact_score": finding.get("impactScore"),
                "has_exploit": finding.get("hasExploit"),
                "has_cisa_kev_exploit": finding.get("hasCisaKevExploit"),
                "status": finding.get("status"),
                "vendor_severity": finding.get("vendorSeverity"),
                "first_detected_at": finding.get("firstDetectedAt"),
                "last_detected_at": finding.get("lastDetectedAt"),
                "resolved_at": finding.get("resolvedAt"),
                "description": finding.get("description"),
                "remediation": finding.get("remediation"),
                "detailed_name": finding.get("detailedName"),
                "version": finding.get("version"),
                "fixed_version": finding.get("fixedVersion"),
                "detection_method": finding.get("detectionMethod"),
                "link": finding.get("link"),
                "portal_url": finding.get("portalUrl"),
                "location_path": finding.get("locationPath"),
                "resolution_reason": finding.get("resolutionReason"),
                "resource_id": asset.get("id"),
                "resource_name": asset.get("name"),
                "resource_type": asset.get("type"),
                "resource_region": asset.get("region"),
                "resource_cloud_platform": asset.get("cloudPlatform"),
                "resource_external_id": asset.get("providerUniqueId")
                or asset.get("imageId")
                or asset.get("ImageExternalId")
                or asset.get("VmExternalId"),
                "resource_status": asset.get("status"),
                "subscription_external_id": asset.get("subscriptionExternalId"),
                "subscription_name": asset.get("subscriptionName"),
                "project_ids": project_ids(projects),
                "project_names": project_names(projects),
            },
        )
    return result


@timeit
def load_vulnerability_findings(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        WizVulnerabilityFindingSchema(),
        data,
        lastupdated=update_tag,
        WIZ_TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        WizVulnerabilityFindingSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    graphql_url: str,
    token: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    lookback_days: int,
    project_id_filter: list[str] | None = None,
    *,
    do_cleanup: bool = True,
) -> None:
    logger.info("Syncing Wiz vulnerability findings for tenant %s", tenant_id)
    since_iso = epoch_days_ago_iso(update_tag, lookback_days)
    raw_findings = get(session, graphql_url, token, since_iso, project_id_filter)
    findings = transform(raw_findings, tenant_id)
    load_vulnerability_findings(neo4j_session, findings, tenant_id, update_tag)
    if do_cleanup:
        cleanup(neo4j_session, common_job_parameters)
