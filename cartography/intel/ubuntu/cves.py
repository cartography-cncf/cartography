import logging
from typing import Any

import neo4j
from requests import Session

from cartography.client.core.tx import load
from cartography.client.core.tx import read_single_value_tx
from cartography.client.core.tx import run_write_query
from cartography.models.ubuntu.cves import UbuntuCVESchema
from cartography.models.ubuntu.feed import UbuntuCVEFeedSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)
_PAGE_SIZE = 20
_FEED_ID = "ubuntu-security-cve-feed"
_SYNC_METADATA_ID = "UbuntuCVE_sync_metadata"
_EPOCH = "2020-01-01T00:00:00+00:00"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_url: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting Ubuntu CVE sync")
    load_feed(neo4j_session, api_url, update_tag)

    last_updated_at = get_last_sync_timestamp(neo4j_session) or _EPOCH
    logger.info("Syncing Ubuntu CVEs updated since %s", last_updated_at)
    raw_cves = get_updated_since(api_url, last_updated_at)

    if raw_cves:
        transformed = transform(raw_cves)
        load_cves(neo4j_session, transformed, update_tag)

        latest_ts = _extract_latest_updated_at(raw_cves)
        if latest_ts:
            save_sync_metadata(neo4j_session, latest_ts, update_tag)
    else:
        logger.info("No new or updated CVEs found")

    # CVEs are never deleted from the Ubuntu database, so no cleanup is needed.
    logger.info("Completed Ubuntu CVE sync")


def get_last_sync_timestamp(neo4j_session: neo4j.Session) -> str | None:
    query = """
    MATCH (s:UbuntuSyncMetadata {id: $sync_id})
    RETURN s.last_updated_at AS last_updated_at
    """
    result = read_single_value_tx(neo4j_session, query, sync_id=_SYNC_METADATA_ID)
    return result


def save_sync_metadata(
    neo4j_session: neo4j.Session,
    last_updated_at: str,
    update_tag: int,
) -> None:
    query = """
    MERGE (s:UbuntuSyncMetadata {id: $sync_id})
    ON CREATE SET s.firstseen = timestamp()
    SET s.last_updated_at = $last_updated_at,
        s.lastupdated = $update_tag
    """
    run_write_query(
        neo4j_session,
        query,
        sync_id=_SYNC_METADATA_ID,
        last_updated_at=last_updated_at,
        update_tag=update_tag,
    )


def _extract_latest_updated_at(raw_cves: list[dict[str, Any]]) -> str | None:
    timestamps = [
        cve["updated_at"] for cve in raw_cves
        if cve.get("updated_at") is not None
    ]
    if not timestamps:
        return None
    return max(timestamps)


@timeit
def get_updated_since(api_url: str, last_updated_at: str) -> list[dict[str, Any]]:
    updated_cves: list[dict[str, Any]] = []
    offset = 0
    session = Session()
    while True:
        logger.debug("Fetching updated Ubuntu CVEs at offset %d", offset)
        response = session.get(
            f"{api_url}/security/cves.json",
            params={
                "limit": str(_PAGE_SIZE),
                "offset": str(offset),
                "sort_by": "updated",
                "order": "descending",
            },
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        cves = data.get("cves", [])
        if not cves:
            break

        found_old = False
        for cve in cves:
            cve_updated = cve.get("updated_at")
            if cve_updated is None or cve_updated <= last_updated_at:
                found_old = True
                break
            updated_cves.append(cve)

        if found_old:
            break
        offset += _PAGE_SIZE

    logger.info("Incremental sync fetched %d updated Ubuntu CVEs", len(updated_cves))
    return updated_cves


@timeit
def transform(raw_cves: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for cve in raw_cves:
        impact = cve.get("impact") or {}
        base_metric_v3 = impact.get("baseMetricV3") or {}
        cvss_v3 = base_metric_v3.get("cvssV3") or {}
        transformed = {
            "id": cve["id"],
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


def load_feed(
    neo4j_session: neo4j.Session,
    api_url: str,
    update_tag: int,
) -> None:
    feed_data = [
        {
            "id": _FEED_ID,
            "name": "Ubuntu Security CVE Feed",
            "url": f"{api_url}/security/cves.json",
        },
    ]
    load(
        neo4j_session,
        UbuntuCVEFeedSchema(),
        feed_data,
        lastupdated=update_tag,
    )


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
        FEED_ID=_FEED_ID,
    )
