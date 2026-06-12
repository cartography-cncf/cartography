import logging
from typing import Any

import neo4j
import requests
from requests.exceptions import HTTPError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.tenable.api import export_and_download
from cartography.models.tenable.tenant import TenableTenantSchema
from cartography.models.tenable.was_findings import TenableWASFindingSchema
from cartography.models.tenable.was_plugins import TenableWASPluginSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_WAS_EXPORT_PATH = "was/v2/findings/export"
_WAS_RESULT_BASE = "was/v2/findings/export"
_WAS_EXPORT_PARAMS: dict[str, Any] = {"num_findings": 500}
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
    findings that have fallen outside it.
    """
    params: dict[str, Any] = dict(_WAS_EXPORT_PARAMS)
    params["filters"] = {
        "last_found": since_epoch,
        "state": _WAS_EXPORT_STATES,
    }
    logger.info(
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


def transform(raw_findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for finding in raw_findings:
        asset = finding.get("asset") or {}
        plugin = finding.get("plugin") or {}

        finding_id = finding.get("finding_id")
        asset_uuid = asset.get("uuid")
        plugin_id = plugin.get("id")

        if not finding_id or not asset_uuid or plugin_id is None:
            logger.warning(
                "Skipping WAS finding with missing finding_id, asset_uuid, or plugin_id"
            )
            continue

        cve_ids: list[str] = plugin.get("cve") or []

        result.append(
            {
                "id": finding_id,
                "asset_uuid": asset_uuid,
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
        vpr_v2 = plugin.get("vpr_v2") or {}
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
                "vpr_v2_score": vpr_v2.get("score"),
                "epss_score": plugin.get("epss_score"),
                "cve_ids": plugin.get("cve") or [],
                "cwe_ids": plugin.get("cwe") or [],
            }
        )
    return result


@timeit
def load_was_findings(
    neo4j_session: neo4j.Session,
    findings: list[dict[str, Any]],
    plugins: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        TenableTenantSchema(),
        [{"id": tenant_id}],
        lastupdated=update_tag,
    )
    # Plugins must exist before findings so the DETECTED_BY target is present.
    load(
        neo4j_session,
        TenableWASPluginSchema(),
        plugins,
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
            logger.warning(
                "Tenable WAS findings export returned 403 Forbidden — "
                "skipping WAS sync. Ensure the API key has Web Application "
                "Scanning permissions."
            )
            return
        raise
    findings = transform(raw_findings)
    plugins = transform_plugins(raw_findings)
    load_was_findings(neo4j_session, findings, plugins, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
