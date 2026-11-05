import logging
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any

from requests import Session

from cartography.intel.cve_metadata.util import parse_utc_datetime
from cartography.util import timeit

logger = logging.getLogger(__name__)

KEV_CATALOG_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
CONNECT_AND_READ_TIMEOUT = (30, 120)

_FORENSIC_TRIAGE = {"Yes": True, "No": False}
_EMPTY_KEV_ENTRY: dict[str, Any] = {
    "kev_date_added": None,
    "kev_due_date": None,
    "kev_ransomware_use": None,
    "kev_forensic_triage": None,
}


@dataclass(frozen=True)
class KevCatalog:
    catalog_version: str | None
    date_released: datetime | None
    entries: dict[str, dict[str, Any]] = field(default_factory=dict)


@timeit
def get_kev_catalog(http_session: Session) -> dict[str, Any]:
    logger.info("Fetching the CISA KEV catalog from %s", KEV_CATALOG_URL)
    response = http_session.get(KEV_CATALOG_URL, timeout=CONNECT_AND_READ_TIMEOUT)
    response.raise_for_status()
    return response.json()


def transform_kev_catalog(raw: dict[str, Any]) -> KevCatalog:
    # The catalog decides is_kev, so an empty or partial one would set CVEs it
    # leaves out to false.
    vulnerabilities = raw["vulnerabilities"]
    if not vulnerabilities:
        raise ValueError("The CISA KEV catalog lists no vulnerabilities.")
    if raw["count"] != len(vulnerabilities):
        raise ValueError(
            f"The CISA KEV catalog declares {raw['count']} vulnerabilities but "
            f"lists {len(vulnerabilities)}.",
        )
    entries: dict[str, dict[str, Any]] = {}
    for vuln in vulnerabilities:
        cve_id = vuln["cveID"]
        forensic_triage = vuln.get("forensicTriage")
        if forensic_triage is not None and forensic_triage not in _FORENSIC_TRIAGE:
            logger.warning(
                "Unexpected KEV forensicTriage value %r for %s; leaving it unset.",
                forensic_triage,
                cve_id,
            )
        entries[cve_id] = {
            "kev_date_added": vuln.get("dateAdded"),
            "kev_due_date": vuln.get("dueDate"),
            "kev_ransomware_use": vuln.get("knownRansomwareCampaignUse"),
            "kev_forensic_triage": _FORENSIC_TRIAGE.get(forensic_triage),
        }
    catalog = KevCatalog(
        catalog_version=raw.get("catalogVersion"),
        date_released=parse_utc_datetime(raw.get("dateReleased")),
        entries=entries,
    )
    logger.info(
        "CISA KEV catalog version %s lists %d CVEs.",
        catalog.catalog_version,
        len(entries),
    )
    return catalog


def merge_kev_into_cves(
    cves: list[dict[str, Any]],
    catalog: KevCatalog | None,
) -> None:
    """
    The catalog is authoritative when it was fetched: a CVE it does not list gets
    is_kev = False even when NVD's embedded copy still lists it. Without a catalog
    (source disabled or fetch failed), is_kev keeps the value NVD supplied, if any.
    """
    for cve in cves:
        if catalog is None:
            cve.update(_EMPTY_KEV_ENTRY)
            cve["is_kev_source"] = "nvd" if cve.get("is_kev") is not None else None
            continue
        entry = catalog.entries.get(cve["id"])
        cve.update(entry or _EMPTY_KEV_ENTRY)
        cve["is_kev"] = entry is not None
        cve["is_kev_source"] = "kev"
