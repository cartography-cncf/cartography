import logging
from typing import Any

import neo4j
import requests
from requests.exceptions import HTTPError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.tenable.api import export_and_download
from cartography.intel.tenable.findings import transform_cves
from cartography.models.tenable.tenant import TenableTenantSchema
from cartography.models.tenable.was_cve import TenableWASCveSchema
from cartography.models.tenable.was_findings import TenableWASFindingSchema
from cartography.models.tenable.was_plugins import TenableWASPluginSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Web App Scanning has its own export API, separate from the vulnerability management
# one. https://developer.tenable.com/reference/was-export-findings
_WAS_EXPORT_PATH = "was/v1/export/vulns"
_WAS_RESULT_BASE = "was/v1/export/vulns"
# The WAS export chunks by asset, not by finding. Tenable's minimum is 50.
_WAS_EXPORT_PARAMS: dict[str, Any] = {"num_assets": 50}
_WAS_EXPORT_STATES = ["OPEN", "REOPENED", "FIXED"]


@timeit
def get(
    session: requests.Session,
    base_url: str,
    since_epoch: int,
) -> list[dict[str, Any]]:
    """
    Export all WAS findings from Tenable with ``last_found >= since_epoch``.

    All states (OPEN, REOPENED, FIXED) are requested so that the graph reflects
    the full picture for the configured window and the cleanup job can remove
    findings that have fallen outside it. Tenable requires ``state`` whenever
    ``last_found`` is given.
    """
    params: dict[str, Any] = dict(_WAS_EXPORT_PARAMS)
    params["filters"] = {
        "last_found": since_epoch,
        "state": _WAS_EXPORT_STATES,
    }
    logger.debug(
        "WAS findings export from %s (last_found >= %d)",
        base_url,
        since_epoch,
    )
    return export_and_download(
        session,
        base_url,
        _WAS_EXPORT_PATH,
        _WAS_RESULT_BASE,
        params,
    )


def _normalize_fqdn(fqdn: str | None) -> str | None:
    # DNS names compare case-insensitively and may carry a trailing root dot.
    if not fqdn:
        return None
    return fqdn.strip().lower().rstrip(".") or None


def _cve_ids(plugin: dict[str, Any]) -> list[str]:
    # Blank entries name no CVE, and Neo4j cannot store a null inside a list.
    return list(dict.fromkeys(cve_id for cve_id in plugin.get("cve") or [] if cve_id))


def transform(raw_findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    skipped: list[str] = []
    for finding in raw_findings:
        asset = finding.get("asset") or {}
        plugin = finding.get("plugin") or {}

        finding_id = finding.get("finding_id")
        asset_uuid = asset.get("uuid")
        plugin_id = plugin.get("id")

        if not finding_id or not asset_uuid or plugin_id is None:
            skipped.append(str(finding_id))
            continue

        result.append(
            {
                "id": finding_id,
                "asset_uuid": asset_uuid,
                "asset_fqdn": _normalize_fqdn(asset.get("fqdn")),
                "plugin_id": plugin_id,
                "scan_uuid": (finding.get("scan") or {}).get("uuid"),
                "url": finding.get("url"),
                "output": finding.get("output"),
                "state": finding.get("state"),
                "severity": finding.get("severity"),
                "severity_id": finding.get("severity_id"),
                "severity_default_id": finding.get("severity_default_id"),
                "severity_modification_type": finding.get("severity_modification_type"),
                "first_found": finding.get("first_found"),
                "last_found": finding.get("last_found"),
                "indexed_at": finding.get("indexed_at"),
                "last_observed": finding.get("last_observed"),
                "last_fixed": finding.get("last_fixed"),
                "input_name": finding.get("input_name"),
                "http_method": finding.get("http_method"),
            }
        )
    if skipped:
        logger.warning(
            "Skipped %d of %d WAS findings that lack finding_id, asset.uuid or plugin.id "
            "(finding_ids: %s)",
            len(skipped),
            len(raw_findings),
            ", ".join(skipped[:5]),
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
                "risk_factor": plugin.get("risk_factor"),
                "type": plugin.get("type"),
                "synopsis": plugin.get("synopsis"),
                "description": plugin.get("description"),
                "solution": plugin.get("solution"),
                "publication_date": plugin.get("publication_date"),
                "modification_date": plugin.get("modification_date"),
                "patch_publication_date": plugin.get("patch_publication_date"),
                "exploitability_ease": plugin.get("exploitability_ease"),
                "in_the_news": plugin.get("in_the_news"),
                "exploited_by_malware": plugin.get("exploited_by_malware"),
                "cvss2_base_score": plugin.get("cvss2_base_score"),
                "cvss3_base_score": plugin.get("cvss3_base_score"),
                "cvss4_base_score": plugin.get("cvss4_base_score"),
                "vpr_score": vpr.get("score"),
                "epss_score": plugin.get("epss_score"),
                "cve_list": _cve_ids(plugin),
                "cwe_ids": plugin.get("cwe") or [],
            }
        )
    return result


@timeit
def load_was_findings(
    neo4j_session: neo4j.Session,
    findings: list[dict[str, Any]],
    plugins: list[dict[str, Any]],
    cves: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        TenableTenantSchema(),
        [{"id": tenant_id}],
        lastupdated=update_tag,
    )
    # Plugins must exist before the CVEs and findings that link to them.
    load(
        neo4j_session,
        TenableWASPluginSchema(),
        plugins,
        lastupdated=update_tag,
        TENABLE_TENANT_ID=tenant_id,
    )
    load(
        neo4j_session,
        TenableWASCveSchema(),
        cves,
        lastupdated=update_tag,
        TENABLE_TENANT_ID=tenant_id,
    )
    load(
        neo4j_session,
        TenableWASFindingSchema(),
        findings,
        lastupdated=update_tag,
        TENABLE_TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(TenableWASFindingSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(TenableWASPluginSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(TenableWASCveSchema(), common_job_parameters).run(
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
        "Syncing Tenable WAS findings for tenant %s (lookback %d days)",
        tenant_id,
        lookback_days,
    )
    since_epoch = update_tag - (lookback_days * 86400)
    try:
        raw_findings = get(session, base_url, since_epoch)
    except HTTPError as e:
        if e.response is not None and e.response.status_code == 403:
            # Return before cleanup: a missing permission must not wipe WAS data that
            # an earlier run, made with a more privileged key, already loaded.
            logger.warning(
                "Tenable WAS findings export returned 403 Forbidden - "
                "skipping WAS sync. Ensure the API key has Web Application "
                "Scanning permissions."
            )
            return
        raise
    findings = transform(raw_findings)
    plugins = transform_plugins(raw_findings)
    cves = transform_cves(plugins, tenant_id)
    load_was_findings(neo4j_session, findings, plugins, cves, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed Tenable WAS finding sync for tenant %s", tenant_id)
