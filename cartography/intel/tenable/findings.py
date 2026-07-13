import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.tenable.api import export_and_download
from cartography.models.tenable.findings import TenableFindingSchema
from cartography.models.tenable.plugins import TenablePluginSchema
from cartography.models.tenable.scans import TenableScanSchema
from cartography.models.tenable.tenant import TenableTenantSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_FINDING_EXPORT_PATH = "vulns/export"
_FINDING_RESULT_BASE = "vulns/export"
_FINDING_EXPORT_PARAMS: dict[str, Any] = {"num_assets": 500}
_FINDING_EXPORT_STATES = ["OPEN", "REOPENED", "FIXED"]


@timeit
def get(
    session: requests.Session,
    base_url: str,
    since_epoch: int,
) -> list[dict[str, Any]]:
    """
    Export all vulnerability findings from Tenable with ``last_found >= since_epoch``.

    All states (OPEN, REOPENED, FIXED) are requested so that the graph reflects
    the full picture for the configured window and the cleanup job can remove
    findings that have fallen outside it.
    """
    params: dict[str, Any] = dict(_FINDING_EXPORT_PARAMS)
    params["filters"] = {
        "last_found": since_epoch,
        "state": _FINDING_EXPORT_STATES,
    }
    logger.info(
        "Findings export from %s (last_found >= %d)",
        base_url,
        since_epoch,
    )
    return export_and_download(
        session,
        base_url,
        _FINDING_EXPORT_PATH,
        _FINDING_RESULT_BASE,
        params,
    )


def transform(raw_findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for finding in raw_findings:
        asset = finding.get("asset") or {}
        plugin = finding.get("plugin") or {}
        port_info = finding.get("port") or {}

        asset_uuid = asset.get("uuid")
        finding_id = finding.get("finding_id")
        plugin_id = plugin.get("id")

        if not asset_uuid or not finding_id or plugin_id is None:
            logger.warning(
                "Skipping finding with missing asset_uuid, finding_id, or plugin_id"
            )
            continue

        cve_ids: list[str] = plugin.get("cve") or []

        result.append(
            {
                "id": finding_id,
                "asset_uuid": asset_uuid,
                "plugin_id": plugin_id,
                "scan_uuid": (finding.get("scan") or {}).get("uuid"),
                "severity": finding.get("severity"),
                "severity_id": finding.get("severity_id"),
                "severity_default_id": finding.get("severity_default_id"),
                "severity_modification_type": finding.get("severity_modification_type"),
                "state": finding.get("state"),
                "first_found": finding.get("first_found"),
                "last_found": finding.get("last_found"),
                "indexed": finding.get("indexed"),
                "source": finding.get("source"),
                "output": finding.get("output"),
                "resurfaced_date": finding.get("resurfaced_date"),
                "time_taken_to_fix": finding.get("time_taken_to_fix"),
                # Port flattened from port sub-object
                "port": port_info.get("port"),
                "protocol": port_info.get("protocol"),
                "service": port_info.get("service"),
                # First CVE for CVEMetadata ontology matching
                "cve_id": cve_ids[0] if cve_ids else None,
                "cve_list": cve_ids,
                "has_cve": "true" if cve_ids else "false",
            }
        )
    return result


def transform_plugins(raw_findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[int] = set()
    result = []
    for finding in raw_findings:
        plugin = finding.get("plugin") or {}
        plugin_id = plugin.get("id")
        if plugin_id is None or plugin_id in seen:
            continue
        seen.add(plugin_id)
        vpr = plugin.get("vpr") or {}
        result.append(
            {
                "id": plugin_id,
                "name": plugin.get("name"),
                "family": plugin.get("family"),
                "family_id": plugin.get("family_id"),
                "description": plugin.get("description"),
                "synopsis": plugin.get("synopsis"),
                "solution": plugin.get("solution"),
                "risk_factor": plugin.get("risk_factor"),
                "has_patch": plugin.get("has_patch"),
                "has_workaround": plugin.get("has_workaround"),
                "vendor_unpatched": plugin.get("vendor_unpatched"),
                "vendor_severity": plugin.get("vendor_severity"),
                "exploit_available": plugin.get("exploit_available"),
                "exploitability_ease": plugin.get("exploitability_ease"),
                "exploit_framework_metasploit": plugin.get(
                    "exploit_framework_metasploit"
                ),
                "patch_publication_date": plugin.get("patch_publication_date"),
                "publication_date": plugin.get("publication_date"),
                "modification_date": plugin.get("modification_date"),
                "vuln_publication_date": plugin.get("vuln_publication_date"),
                "cvss_base_score": plugin.get("cvss_base_score"),
                "cvss_temporal_score": plugin.get("cvss_temporal_score"),
                "cvss3_base_score": plugin.get("cvss3_base_score"),
                "cvss3_temporal_score": plugin.get("cvss3_temporal_score"),
                "cvss4_base_score": plugin.get("cvss4_base_score"),
                "vpr_score": vpr.get("score"),
                "epss_score": plugin.get("epss_score"),
                "cve_list": plugin.get("cve") or [],
                "type": plugin.get("type"),
            }
        )
    return result


def transform_scans(raw_findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result = []
    for finding in raw_findings:
        scan = finding.get("scan") or {}
        scan_uuid = scan.get("uuid")
        if not scan_uuid or scan_uuid in seen:
            continue
        seen.add(scan_uuid)
        result.append(
            {
                "id": scan_uuid,
                "schedule_uuid": scan.get("schedule_uuid"),
                "started_at": scan.get("started_at"),
                "last_scan_target": scan.get("last_scan_target"),
            }
        )
    return result


@timeit
def load_findings(
    neo4j_session: neo4j.Session,
    findings: list[dict[str, Any]],
    plugins: list[dict[str, Any]],
    scans: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        TenableTenantSchema(),
        [{"id": tenant_id}],
        lastupdated=update_tag,
    )
    # Plugins and scans must exist before findings so outward rel targets are present.
    load(
        neo4j_session,
        TenablePluginSchema(),
        plugins,
        lastupdated=update_tag,
        TENABLE_TENANT_ID=tenant_id,
    )
    load(
        neo4j_session,
        TenableScanSchema(),
        scans,
        lastupdated=update_tag,
        TENABLE_TENANT_ID=tenant_id,
    )
    load(
        neo4j_session,
        TenableFindingSchema(),
        findings,
        lastupdated=update_tag,
        TENABLE_TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(TenableFindingSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(TenablePluginSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(TenableScanSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    base_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    lookback_days: int = 180,
) -> None:
    logger.info(
        "Syncing Tenable findings for tenant %s (lookback %d days)",
        tenant_id,
        lookback_days,
    )
    since_epoch = update_tag - (lookback_days * 86400)
    raw_findings = get(session, base_url, since_epoch)
    findings = transform(raw_findings)
    plugins = transform_plugins(raw_findings)
    scans = transform_scans(raw_findings)
    load_findings(neo4j_session, findings, plugins, scans, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
