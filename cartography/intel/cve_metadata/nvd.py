import logging
import time
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from functools import reduce
from typing import Any

import neo4j
from requests import Session

from cartography.client.core.tx import read_list_of_values_tx
from cartography.util import timeit

logger = logging.getLogger(__name__)

CONNECT_AND_READ_TIMEOUT = (30, 120)
BATCH_SIZE_DAYS = 120
RESULTS_PER_PAGE = 2000
SLEEP_TIME = 6.0


@timeit
def get_cve_ids_from_graph(neo4j_session: neo4j.Session) -> list[str]:
    """Query Neo4j for all CVE node IDs present in the graph."""
    query = """
    MATCH (c:CVE)
    WHERE c.id STARTS WITH "CVE"
    RETURN DISTINCT c.id
    """
    return [str(cve_id) for cve_id in read_list_of_values_tx(neo4j_session, query)]


def _call_cves_api(
    http_session: Session,
    url: str,
    params: dict[str, Any],
) -> dict[Any, Any]:
    """Paginate through the NVD CVE API and return merged results."""
    params["startIndex"] = 0
    params["resultsPerPage"] = RESULTS_PER_PAGE
    headers = {"Content-Type": "application/json"}
    results: dict[Any, Any] = {}

    while True:
        logger.info("Calling NVD API at %s with params %s", url, params)
        res = http_session.get(
            url,
            params=params,
            headers=headers,
            timeout=CONNECT_AND_READ_TIMEOUT,
        )
        res.raise_for_status()
        data = res.json()

        results["format"] = data["format"]
        results["version"] = data["version"]
        results["timestamp"] = data["timestamp"]
        results["totalResults"] = data["totalResults"]
        results["vulnerabilities"] = results.get("vulnerabilities", []) + data.get(
            "vulnerabilities",
            [],
        )

        total_results = data["totalResults"]
        params["startIndex"] += data["resultsPerPage"]
        if params["startIndex"] >= total_results:
            break
        time.sleep(SLEEP_TIME)

    return results


@timeit
def get_cves_in_date_range(
    http_session: Session,
    nist_cve_url: str,
    start_date: datetime,
    end_date: datetime,
) -> dict[Any, Any]:
    """Fetch CVEs from NVD in 120-day batches over a date range."""
    cves: dict[Any, Any] = {}
    batch_size = timedelta(days=BATCH_SIZE_DAYS)
    current_start = start_date

    while current_start < end_date:
        current_end = min(current_start + batch_size, end_date)
        params = {
            "lastModStartDate": current_start.strftime("%Y-%m-%dT%H:%M:%S"),
            "lastModEndDate": current_end.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        logger.info(
            "Querying NVD for CVEs modified between %s and %s",
            current_start,
            current_end,
        )
        batch = _call_cves_api(http_session, nist_cve_url, params)

        if not cves:
            cves = batch
        else:
            cves["vulnerabilities"] = cves.get("vulnerabilities", []) + batch.get(
                "vulnerabilities", []
            )
            cves["totalResults"] = cves.get("totalResults", 0) + batch.get(
                "totalResults", 0
            )

        current_start = current_end

    return cves


def _get_primary_metric(metrics: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    if metrics is None:
        return None
    for metric in metrics:
        if metric["type"] == "Primary":
            return metric
    return metrics[0] if metrics else None


def transform_cves(
    cve_json: dict[Any, Any],
    cve_ids_in_graph: set[str],
) -> dict[str, dict[Any, Any]]:
    """
    Transform NVD CVE data, filtering to only CVEs present in the graph.
    Returns a dict keyed by CVE ID for easy merging.
    """
    cves: dict[str, dict[Any, Any]] = {}
    for data in cve_json.get("vulnerabilities", []):
        try:
            cve = data["cve"]
            if cve["id"] not in cve_ids_in_graph:
                continue

            # English descriptions
            cve["descriptions_en"] = [
                desc["value"]
                for desc in cve.get("descriptions", [])
                if desc["lang"] == "en"
            ]

            # Reference URLs
            cve["references_urls"] = [ref["url"] for ref in cve.get("references", [])]

            # Weaknesses / CWEs
            if cve.get("weaknesses"):
                weakness_descriptions: list[dict[str, str]] = reduce(
                    lambda x, y: x + y,
                    [w["description"] for w in cve["weaknesses"]],
                    [],
                )
                cve["weaknesses"] = [
                    d["value"] for d in weakness_descriptions if d["lang"] == "en"
                ]

            # CVSS v3.1 metrics
            cvss31_metrics = cve.get("metrics", {}).get("cvssMetricV31")
            cvss31 = _get_primary_metric(cvss31_metrics)
            if cvss31:
                cvss_data = cvss31.get("cvssData", {})
                cve["vectorString"] = cvss_data.get("vectorString")
                cve["attackVector"] = cvss_data.get("attackVector")
                cve["attackComplexity"] = cvss_data.get("attackComplexity")
                cve["privilegesRequired"] = cvss_data.get("privilegesRequired")
                cve["userInteraction"] = cvss_data.get("userInteraction")
                cve["scope"] = cvss_data.get("scope")
                cve["confidentialityImpact"] = cvss_data.get("confidentialityImpact")
                cve["integrityImpact"] = cvss_data.get("integrityImpact")
                cve["availabilityImpact"] = cvss_data.get("availabilityImpact")
                cve["baseScore"] = cvss_data.get("baseScore")
                cve["baseSeverity"] = cvss_data.get("baseSeverity")
                cve["exploitabilityScore"] = cvss31.get("exploitabilityScore")
                cve["impactScore"] = cvss31.get("impactScore")

            # CISA KEV fields are already top-level in cve dict if present:
            # cisaExploitAdd, cisaActionDue, cisaRequiredAction, cisaVulnerabilityName

        except Exception:
            logger.error("Failed to transform CVE data: %s", data)
            raise
        cves[cve["id"]] = cve
    return cves


def merge_nvd_into_cves(
    cves: list[dict[str, Any]],
    nvd_data: dict[str, dict[Any, Any]],
) -> None:
    """Merge NVD metadata into CVE dicts in-place."""
    for cve in cves:
        nvd_entry = nvd_data.get(cve["id"])
        if nvd_entry:
            cve.update(nvd_entry)


def get_and_transform_nvd_cves(
    http_session: Session,
    nist_cve_url: str,
    cve_ids_in_graph: set[str],
) -> dict[str, dict[Any, Any]]:
    """
    Fetch all recently modified CVEs from NVD and filter to those in the graph.
    Uses a 2-year lookback window to capture recent modifications.
    """
    end_date = datetime.now(tz=timezone.utc)
    start_date = end_date - timedelta(days=730)

    logger.info(
        "Fetching NVD CVE data from %s to %s for %d CVEs in graph",
        start_date,
        end_date,
        len(cve_ids_in_graph),
    )
    cve_json = get_cves_in_date_range(http_session, nist_cve_url, start_date, end_date)
    return transform_cves(cve_json, cve_ids_in_graph)
