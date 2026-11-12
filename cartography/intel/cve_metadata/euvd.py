"""
ENISA EU Vulnerability Database (EUVD): fills the CVSS score, description,
references, and publication date of CVEs that NVD has not scored.

EUVD has no bulk download and no multi-CVE lookup, so the sync asks it about
one CVE per request. To keep that small, it asks only about CVEs that NVD left
without a CVSS score and that are not rejected.
"""

import logging
from datetime import datetime
from datetime import timezone
from typing import Any

from requests import Session

from cartography.util import timeit

logger = logging.getLogger(__name__)

EUVD_SEARCH_URL = "https://euvdservices.enisa.europa.eu/api/search"
CONNECT_AND_READ_TIMEOUT = (30, 60)
# The search also matches CVE ids inside descriptions, so ask for a few records
# and keep the one that lists the CVE as an alias.
SEARCH_PAGE_SIZE = 10
EUVD_DATE_FORMAT = "%b %d, %Y, %I:%M:%S %p"

# Vector abbreviations expanded to the values NVD uses in cvssData, so the
# effect_tags fallback reads EUVD-filled CVEs the same way it reads NVD ones.
_CVSS_V3_METRICS = {
    "AV": (
        "attackVector",
        {"N": "NETWORK", "A": "ADJACENT_NETWORK", "L": "LOCAL", "P": "PHYSICAL"},
    ),
    "AC": ("attackComplexity", {"L": "LOW", "H": "HIGH"}),
    "PR": ("privilegesRequired", {"N": "NONE", "L": "LOW", "H": "HIGH"}),
    "UI": ("userInteraction", {"N": "NONE", "R": "REQUIRED"}),
    "S": ("scope", {"U": "UNCHANGED", "C": "CHANGED"}),
    "C": ("confidentialityImpact", {"N": "NONE", "L": "LOW", "H": "HIGH"}),
    "I": ("integrityImpact", {"N": "NONE", "L": "LOW", "H": "HIGH"}),
    "A": ("availabilityImpact", {"N": "NONE", "L": "LOW", "H": "HIGH"}),
}
# NVD's CVSS 4.0 cvssData has no confidentiality, integrity, or availability
# impact under those names, so neither does an EUVD 4.0 score.
_CVSS_V4_METRICS = {
    "AV": (
        "attackVector",
        {"N": "NETWORK", "A": "ADJACENT", "L": "LOCAL", "P": "PHYSICAL"},
    ),
    "AC": ("attackComplexity", {"L": "LOW", "H": "HIGH"}),
    "PR": ("privilegesRequired", {"N": "NONE", "L": "LOW", "H": "HIGH"}),
    "UI": ("userInteraction", {"N": "NONE", "P": "PASSIVE", "A": "ACTIVE"}),
}
_METRICS_BY_VERSION = {
    "3.0": _CVSS_V3_METRICS,
    "3.1": _CVSS_V3_METRICS,
    "4.0": _CVSS_V4_METRICS,
}

_FILLED_FIELDS = ("description_en", "references_urls", "published")
_CVSS_FIELDS = (
    "cvss_version",
    "vectorString",
    "baseScore",
    "baseSeverity",
    *(key for key, _ in _CVSS_V3_METRICS.values()),
)


def _split_lines(value: str | None) -> list[str]:
    return [line.strip() for line in (value or "").splitlines() if line.strip()]


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.strptime(value, EUVD_DATE_FORMAT)
    except ValueError:
        logger.debug("Unparseable EUVD date %r", value)
        return None
    return parsed.replace(tzinfo=timezone.utc)


def _severity(score: float, version: str) -> str:
    if version == "2.0":
        if score >= 7.0:
            return "HIGH"
        return "MEDIUM" if score >= 4.0 else "LOW"
    if score >= 9.0:
        return "CRITICAL"
    if score >= 7.0:
        return "HIGH"
    if score >= 4.0:
        return "MEDIUM"
    return "LOW" if score > 0 else "NONE"


def _parse_vector(vector: str, version: str) -> dict[str, str]:
    metrics = _METRICS_BY_VERSION.get(version, {})
    parsed: dict[str, str] = {}
    for part in vector.split("/"):
        abbreviation, _, value = part.partition(":")
        if abbreviation in metrics:
            key, values = metrics[abbreviation]
            if value in values:
                parsed[key] = values[value]
    return parsed


def transform_euvd_record(record: dict[str, Any]) -> dict[str, Any]:
    transformed: dict[str, Any] = {
        "euvd_id": record["id"],
        "description_en": record.get("description") or None,
        "references_urls": _split_lines(record.get("references")),
        "published": _parse_date(record.get("datePublished")),
    }
    score = record.get("baseScore")
    version = record.get("baseScoreVersion")
    # EUVD reports an unscored record as a base score of 0 with no version.
    if score and version:
        vector = record.get("baseScoreVector") or None
        transformed.update(
            {
                "cvss_version": version,
                "vectorString": vector,
                "baseScore": float(score),
                "baseSeverity": _severity(float(score), version),
                **(_parse_vector(vector, version) if vector else {}),
            },
        )
    return transformed


def _find_record(items: list[dict[str, Any]], cve_id: str) -> dict[str, Any] | None:
    for item in items:
        if cve_id in _split_lines(item.get("aliases")):
            return item
    return None


def needs_euvd(cve: dict[str, Any]) -> bool:
    return cve.get("baseScore") is None and cve.get("vulnStatus") != "Rejected"


@timeit
def get_euvd_records(
    http_session: Session,
    cve_ids: list[str],
) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for cve_id in cve_ids:
        response = http_session.get(
            EUVD_SEARCH_URL,
            params={"text": cve_id, "size": str(SEARCH_PAGE_SIZE)},
            timeout=CONNECT_AND_READ_TIMEOUT,
        )
        response.raise_for_status()
        record = _find_record(response.json().get("items") or [], cve_id)
        if record is not None:
            records[cve_id] = transform_euvd_record(record)
    return records


def merge_euvd_into_cves(
    cves: list[dict[str, Any]],
    euvd_records: dict[str, dict[str, Any]],
) -> None:
    """EUVD only fills what NVD left empty; it never replaces an NVD value."""
    for cve in cves:
        record = euvd_records.get(cve["id"])
        if record is None:
            continue
        cve["euvd_id"] = record["euvd_id"]
        for key in _FILLED_FIELDS:
            if not cve.get(key) and record.get(key):
                cve[key] = record[key]
        if cve.get("baseScore") is None and record.get("baseScore") is not None:
            for key in _CVSS_FIELDS:
                if key in record:
                    cve[key] = record[key]
            cve["cvss_source"] = "euvd"
