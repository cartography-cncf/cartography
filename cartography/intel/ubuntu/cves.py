import logging
from typing import Any

import neo4j
from requests import Session

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.ubuntu.cves import UbuntuCVESchema
from cartography.models.ubuntu.feed import UbuntuCVEFeedSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)
_PAGE_SIZE = 20
_FEED_ID = "ubuntu-security-cve-feed"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_url: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting Ubuntu CVE sync")
    load_feed(neo4j_session, api_url, update_tag)
    raw_cves = get(api_url)
    transformed = transform(raw_cves)
    load_cves(neo4j_session, transformed, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed Ubuntu CVE sync")


@timeit
def get(api_url: str) -> list[dict[str, Any]]:
    all_cves: list[dict[str, Any]] = []
    offset = 0
    session = Session()
    while True:
        logger.debug("Fetching Ubuntu CVEs at offset %d", offset)
        response = session.get(
            f"{api_url}/security/cves.json",
            params={"limit": str(_PAGE_SIZE), "offset": str(offset), "order": "oldest"},
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        cves = data.get("cves", [])
        all_cves.extend(cves)
        total = data.get("total_results", 0)
        if not cves or len(all_cves) >= total:
            break
        offset += _PAGE_SIZE
    logger.debug("Fetched %d Ubuntu CVEs total", len(all_cves))
    return all_cves


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


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        UbuntuCVESchema(),
        {**common_job_parameters, "FEED_ID": _FEED_ID},
    ).run(neo4j_session)
