import logging
from collections.abc import Iterator
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import read_single_value_tx
from cartography.client.core.tx import run_write_query
from cartography.intel.ubuntu.feed import FEED_ID
from cartography.intel.ubuntu.util import retryable_session
from cartography.models.ubuntu.cves import UbuntuCVESchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)
_PAGE_SIZE = 20
_SYNC_METADATA_ID = "UbuntuCVE_sync_metadata"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_url: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting Ubuntu CVE sync")

    metadata = get_sync_metadata(neo4j_session)

    if metadata["full_sync_complete"]:
        _run_incremental_sync(
            neo4j_session,
            api_url,
            update_tag,
            metadata["last_updated_at"],
        )
    else:
        _run_full_sync(neo4j_session, api_url, update_tag, metadata["full_sync_offset"])

    logger.info("Completed Ubuntu CVE sync")


def _run_full_sync(
    neo4j_session: neo4j.Session,
    api_url: str,
    update_tag: int,
    start_offset: int,
) -> None:
    if start_offset > 0:
        logger.info("Resuming full CVE sync from offset %d", start_offset)
    else:
        logger.info("Running full CVE ingestion")

    total = 0
    current_offset = start_offset
    for page in _fetch_cves(api_url, start_offset=start_offset):
        transformed = transform(page)
        load_cves(neo4j_session, transformed, update_tag)
        total += len(transformed)
        current_offset += _PAGE_SIZE
        save_sync_metadata(
            neo4j_session,
            update_tag,
            full_sync_complete=False,
            full_sync_offset=current_offset,
            last_updated_at=None,
        )

    watermark = _get_max_updated_at(neo4j_session)
    save_sync_metadata(
        neo4j_session,
        update_tag,
        full_sync_complete=True,
        full_sync_offset=0,
        last_updated_at=watermark,
    )
    logger.info(
        "Full sync complete: loaded %d Ubuntu CVEs (watermark=%s)",
        total,
        watermark,
    )


def _run_incremental_sync(
    neo4j_session: neo4j.Session,
    api_url: str,
    update_tag: int,
    last_updated_at: str | None,
) -> None:
    logger.info("Running incremental CVE sync (watermark=%s)", last_updated_at)

    total = 0
    best_watermark: str | None = None
    for page in _fetch_cves(api_url, since=last_updated_at):
        transformed = transform(page)
        load_cves(neo4j_session, transformed, update_tag)
        total += len(transformed)
        latest_ts = _extract_latest_updated_at(page)
        if latest_ts and (best_watermark is None or latest_ts > best_watermark):
            best_watermark = latest_ts

    if best_watermark:
        save_sync_metadata(
            neo4j_session,
            update_tag,
            full_sync_complete=True,
            full_sync_offset=0,
            last_updated_at=best_watermark,
        )
        logger.info(
            "Incremental sync complete: loaded %d CVEs (new watermark=%s)",
            total,
            best_watermark,
        )
    else:
        logger.info("No new or updated CVEs found")


def get_sync_metadata(neo4j_session: neo4j.Session) -> dict[str, Any]:
    def _read_tx(tx: neo4j.ManagedTransaction) -> neo4j.Record | None:
        return tx.run(
            """
            MATCH (s:UbuntuSyncMetadata {id: $sync_id})
            RETURN s.full_sync_complete AS full_sync_complete,
                   s.full_sync_offset AS full_sync_offset,
                   s.last_updated_at AS last_updated_at
            """,
            sync_id=_SYNC_METADATA_ID,
        ).single()

    result = neo4j_session.execute_read(_read_tx)
    if result is None:
        return {
            "full_sync_complete": False,
            "full_sync_offset": 0,
            "last_updated_at": None,
        }
    return {
        "full_sync_complete": result["full_sync_complete"] or False,
        "full_sync_offset": result["full_sync_offset"] or 0,
        "last_updated_at": result["last_updated_at"],
    }


def save_sync_metadata(
    neo4j_session: neo4j.Session,
    update_tag: int,
    *,
    full_sync_complete: bool,
    full_sync_offset: int,
    last_updated_at: str | None,
) -> None:
    query = """
    MERGE (s:UbuntuSyncMetadata {id: $sync_id})
    ON CREATE SET s.firstseen = timestamp()
    SET s.full_sync_complete = $full_sync_complete,
        s.full_sync_offset = $full_sync_offset,
        s.last_updated_at = $last_updated_at,
        s.lastupdated = $update_tag
    """
    run_write_query(
        neo4j_session,
        query,
        sync_id=_SYNC_METADATA_ID,
        full_sync_complete=full_sync_complete,
        full_sync_offset=full_sync_offset,
        last_updated_at=last_updated_at,
        update_tag=update_tag,
    )


def _extract_latest_updated_at(raw_cves: list[dict[str, Any]]) -> str | None:
    timestamps = [
        cve["updated_at"] for cve in raw_cves if cve.get("updated_at") is not None
    ]
    if not timestamps:
        return None
    return max(timestamps)


def _get_max_updated_at(neo4j_session: neo4j.Session) -> str | None:
    result = read_single_value_tx(
        neo4j_session,
        "MATCH (c:UbuntuCVE) RETURN max(c.updated_at) AS max_updated_at",
    )
    return str(result) if result is not None else None


@timeit
def _fetch_cves(
    api_url: str,
    *,
    since: str | None = None,
    start_offset: int = 0,
) -> Iterator[list[dict[str, Any]]]:
    """Yield pages of CVEs from the Ubuntu Security API.

    Full sync (since=None): fetches all CVEs sorted by published date ascending,
    starting from start_offset for resume capability.

    Incremental (since set): fetches CVEs updated after the watermark, sorted by
    updated_at descending, stopping when it reaches already-seen data.
    """
    offset = start_offset
    total_fetched = 0
    session = retryable_session()

    if since is None:
        params_base: dict[str, str] = {"limit": str(_PAGE_SIZE), "order": "ascending"}
    else:
        params_base = {
            "limit": str(_PAGE_SIZE),
            "sort_by": "updated",
            "order": "descending",
        }

    while True:
        logger.debug("Fetching Ubuntu CVEs at offset %d", offset)
        response = session.get(
            f"{api_url}/security/cves.json",
            params={**params_base, "offset": str(offset)},
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        cves = data.get("cves", [])
        if not cves:
            break

        if since is not None:
            page: list[dict[str, Any]] = []
            found_old = False
            for cve in cves:
                cve_updated = cve.get("updated_at")
                if cve_updated is None or cve_updated <= since:
                    found_old = True
                    break
                page.append(cve)

            if page:
                yield page
                total_fetched += len(page)

            if found_old:
                break
        else:
            yield cves
            total_fetched += len(cves)
            if total_fetched + start_offset >= data.get("total_results", 0):
                break

        offset += _PAGE_SIZE

    logger.debug("Fetched %d Ubuntu CVEs", total_fetched)


@timeit
def transform(raw_cves: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for cve in raw_cves:
        impact = cve.get("impact") or {}
        base_metric_v3 = impact.get("baseMetricV3") or {}
        cvss_v3 = base_metric_v3.get("cvssV3") or {}
        raw_id = cve["id"]
        transformed = {
            "id": f"USV|{raw_id}",
            "cve_id": raw_id,
            "description": cve.get("description"),
            "ubuntu_description": cve.get("ubuntu_description"),
            "priority": cve.get("priority"),
            "status": cve.get("status"),
            "cvss3": cve.get("cvss3"),
            "published": cve.get("published"),
            "updated_at": cve.get("updated_at"),
            "codename": cve.get("codename"),
            "mitigation": cve.get("mitigation"),
            "attack_vector": cvss_v3.get("attackVector"),
            "attack_complexity": cvss_v3.get("attackComplexity"),
            "base_score": cvss_v3.get("baseScore"),
            "base_severity": cvss_v3.get("baseSeverity"),
            "confidentiality_impact": cvss_v3.get("confidentialityImpact"),
            "integrity_impact": cvss_v3.get("integrityImpact"),
            "availability_impact": cvss_v3.get("availabilityImpact"),
        }
        result.append(transformed)
    return result


def load_cves(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        UbuntuCVESchema(),
        data,
        lastupdated=update_tag,
        FEED_ID=FEED_ID,
    )
