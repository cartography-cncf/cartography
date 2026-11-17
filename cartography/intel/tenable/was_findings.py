import logging
from typing import Any

import neo4j
import requests
from requests.exceptions import HTTPError

from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
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
# `include_unlicensed` (a JSON boolean, default false) adds the findings of assets that
# have no WAS license. Without it those findings vanish from the export when a license
# lapses and cleanup then deletes them, although Tenable still reports them. Such assets
# are not rescanned, so check `last_found` before trusting a finding's state.
_WAS_EXPORT_PARAMS: dict[str, Any] = {"num_assets": 50, "include_unlicensed": True}
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
    for finding in raw_findings:
        asset = finding["asset"]
        plugin = finding["plugin"]

        asset_uuid = asset["uuid"]
        finding_id = finding["finding_id"]
        plugin_id = plugin["id"]
        if not asset_uuid or not finding_id or plugin_id is None:
            # Raise rather than skip: cleanup would otherwise delete the stored node
            # of a finding that Tenable still reports.
            raise ValueError(
                "Tenable WAS finding requires non-empty asset.uuid and finding_id, "
                "and a non-null plugin.id"
            )

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
def keep_cves_named_by_was_plugins(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    update_tag: int,
) -> None:
    """
    Carry forward the CVEs that WAS plugins from an earlier sync still name.

    `TenableCve` is shared with the vulnerability management sync, whose cleanup runs
    before the WAS sync and deletes every tenant CVE it did not load in this run. That
    would delete a CVE only WAS plugins name, with its `HAS_CVE` edges, and it would
    stay gone if the WAS sync is then skipped or fails. Call this before the
    vulnerability management sync so those CVEs survive its cleanup. A CVE that no
    WAS plugin names any more is not carried and is removed by the next run's cleanup.

    The tenant `RESOURCE` edge is refreshed together with the node. That cleanup also
    deletes stale `RESOURCE` edges, and a CVE left without one falls outside the
    tenant-scoped cleanup, so it would never be removed.
    """
    run_write_query(
        neo4j_session,
        """
        MATCH (tenant:TenableTenant {id: $TENABLE_TENANT_ID})
              -[:RESOURCE]->(:TenableWASPlugin)-[:HAS_CVE]->(cve:TenableCve)
              <-[edge:RESOURCE]-(tenant)
        SET cve.lastupdated = $UPDATE_TAG, edge.lastupdated = $UPDATE_TAG
        """,
        TENABLE_TENANT_ID=tenant_id,
        UPDATE_TAG=update_tag,
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
