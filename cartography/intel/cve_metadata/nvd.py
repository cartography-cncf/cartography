import json
import logging
import tempfile
import time
import zipfile
from datetime import datetime
from functools import reduce
from io import BytesIO
from typing import Any

from requests import Session

from cartography.util import timeit

logger = logging.getLogger(__name__)

NVD_API_BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
NVD_FEED_BASE_URL = "https://nvd.nist.gov/feeds/json/cve/2.0"
CONNECT_AND_READ_TIMEOUT = (30, 120)
# NVD API rate limits: 50 req/30s with key. 0.6s/req would hit the limit exactly;
# keep a margin at 1s.
API_SLEEP_TIME = 1.0


def _extract_years_from_cve_ids(cve_ids: set[str]) -> set[str]:
    """Extract unique years from CVE IDs (e.g., CVE-2023-12345 → 2023)."""
    years: set[str] = set()
    for cve_id in cve_ids:
        parts = cve_id.split("-")
        if len(parts) >= 2:
            years.add(parts[1])
    return years


@timeit
def _fetch_cve_from_api(
    http_session: Session,
    cve_id: str,
    api_key: str,
) -> dict[Any, Any] | None:
    """Fetch a single CVE from the NVD API v2.0. Returns the raw `cve` dict or None."""
    response = http_session.get(
        NVD_API_BASE_URL,
        params={"cveId": cve_id},
        headers={"apiKey": api_key, "Content-Type": "application/json"},
        timeout=CONNECT_AND_READ_TIMEOUT,
    )
    response.raise_for_status()
    vulnerabilities = response.json().get("vulnerabilities", [])
    if not vulnerabilities:
        return None
    return vulnerabilities[0].get("cve")


@timeit
def _download_nvd_feed(http_session: Session, year: str) -> dict[Any, Any]:
    """Download and extract a yearly NVD JSON feed zip into a temp directory."""
    url = f"{NVD_FEED_BASE_URL}/nvdcve-2.0-{year}.json.zip"
    logger.debug("Downloading NVD feed for year %s from %s", year, url)

    response = http_session.get(url, timeout=CONNECT_AND_READ_TIMEOUT)
    response.raise_for_status()

    with tempfile.TemporaryDirectory() as tmp_dir:
        with zipfile.ZipFile(BytesIO(response.content)) as zf:
            zf.extractall(tmp_dir)
            json_filename = zf.namelist()[0]
            with open(f"{tmp_dir}/{json_filename}") as f:
                return json.load(f)


def _get_primary_metric(metrics: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    if metrics is None:
        return None
    for metric in metrics:
        if metric["type"] == "Primary":
            return metric
    return metrics[0] if metrics else None


# CVSS version preference order: v4.0 > v3.1 > v3.0 > v2.0
_CVSS_PREFERENCE = [
    ("cvssMetricV40", "4.0"),
    ("cvssMetricV31", "3.1"),
    ("cvssMetricV30", "3.0"),
    ("cvssMetricV2", "2.0"),
]


def _get_best_cvss(
    metrics: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    """Return the best available CVSS metric and its version string."""
    for key, version in _CVSS_PREFERENCE:
        metric = _get_primary_metric(metrics.get(key))
        if metric:
            return metric, version
    return None, None


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

            # English description (join multiple entries into one string)
            en_descriptions = [
                desc["value"]
                for desc in cve.get("descriptions", [])
                if desc["lang"] == "en"
            ]
            cve["description_en"] = (
                "\n".join(en_descriptions) if en_descriptions else None
            )

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

            # CVSS metrics — prefer v4.0, fallback v3.1, v3.0, v2.0
            metrics = cve.get("metrics", {})
            cvss_metric, cvss_version = _get_best_cvss(metrics)
            if cvss_metric:
                cvss_data = cvss_metric.get("cvssData", {})
                cve["cvss_version"] = cvss_version
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
                cve["exploitabilityScore"] = cvss_metric.get("exploitabilityScore")
                cve["impactScore"] = cvss_metric.get("impactScore")

            # Parse date strings to datetime objects
            for date_field in ("published", "lastModified"):
                if cve.get(date_field):
                    cve[date_field] = datetime.fromisoformat(cve[date_field])

            # CISA KEV fields are already top-level in cve dict if present
            cve["is_kev"] = cve.get("cisaExploitAdd") is not None

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


@timeit
def _get_nvd_cves_from_api(
    http_session: Session,
    cve_ids_in_graph: set[str],
    api_key: str,
) -> dict[str, dict[Any, Any]]:
    """Fetch CVEs one-by-one from the NVD API, transforming each response."""
    logger.info(
        "Fetching %d CVEs from NVD API v2.0 (one request per CVE)",
        len(cve_ids_in_graph),
    )
    all_cves: dict[str, dict[Any, Any]] = {}
    for cve_id in sorted(cve_ids_in_graph):
        raw_cve = _fetch_cve_from_api(http_session, cve_id, api_key)
        if raw_cve is None:
            logger.debug("CVE %s not found in NVD, skipping.", cve_id)
            continue
        transformed = transform_cves(
            {"vulnerabilities": [{"cve": raw_cve}]},
            cve_ids_in_graph,
        )
        all_cves.update(transformed)
        time.sleep(API_SLEEP_TIME)
    return all_cves


@timeit
def _get_nvd_cves_from_feeds(
    http_session: Session,
    cve_ids_in_graph: set[str],
) -> dict[str, dict[Any, Any]]:
    """Download NVD yearly feed files for the years matching CVE IDs in the graph."""
    years = _extract_years_from_cve_ids(cve_ids_in_graph)
    logger.info(
        "Downloading NVD feeds for years %s to enrich %d CVEs",
        sorted(years),
        len(cve_ids_in_graph),
    )
    all_cves: dict[str, dict[Any, Any]] = {}
    for year in sorted(years):
        feed_data = _download_nvd_feed(http_session, year)
        year_cves = transform_cves(feed_data, cve_ids_in_graph)
        all_cves.update(year_cves)
        logger.debug("Year %s: found %d matching CVEs.", year, len(year_cves))
    return all_cves


@timeit
def get_and_transform_nvd_cves(
    http_session: Session,
    cve_ids_in_graph: set[str],
    api_key: str | None = None,
) -> dict[str, dict[Any, Any]]:
    """
    Enrich CVEs with NVD metadata. Uses the NVD API v2.0 per-CVE when an API key
    is provided (fresher data, no unused downloads); otherwise falls back to
    yearly JSON feed downloads.
    """
    if api_key:
        return _get_nvd_cves_from_api(http_session, cve_ids_in_graph, api_key)
    return _get_nvd_cves_from_feeds(http_session, cve_ids_in_graph)
