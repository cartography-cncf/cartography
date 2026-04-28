import logging
from typing import Any

from requests import Session

from cartography.util import timeit

logger = logging.getLogger(__name__)

EPSS_API_URL = "https://api.first.org/data/v1/epss"
CONNECT_AND_READ_TIMEOUT = (30, 120)
# EPSS API accepts up to 100 CVEs per request
BATCH_SIZE = 100


@timeit
def get_epss_scores(
    http_session: Session,
    cve_ids: list[str],
) -> dict[str, dict[str, Any]]:
    """
    Fetch EPSS scores for a list of CVE IDs.
    Returns a dict keyed by CVE ID with epss_score and epss_percentile.
    """
    results: dict[str, dict[str, Any]] = {}

    for i in range(0, len(cve_ids), BATCH_SIZE):
        batch = cve_ids[i : i + BATCH_SIZE]
        cve_param = ",".join(batch)
        logger.info(
            "Fetching EPSS scores for %d CVEs (batch %d/%d)",
            len(batch),
            i // BATCH_SIZE + 1,
            (len(cve_ids) + BATCH_SIZE - 1) // BATCH_SIZE,
        )
        response = http_session.get(
            EPSS_API_URL,
            params={"cve": cve_param},
            timeout=CONNECT_AND_READ_TIMEOUT,
        )
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError:
            logger.warning(
                "EPSS batch %d returned invalid JSON, skipping.", i // BATCH_SIZE + 1
            )
            continue

        for entry in data.get("data", []):
            try:
                results[entry["cve"]] = {
                    "epss_score": float(entry["epss"]),
                    "epss_percentile": float(entry["percentile"]),
                }
            except (KeyError, ValueError, TypeError):
                logger.warning("Skipping malformed EPSS entry: %s", entry)
                continue

    logger.debug("Fetched EPSS scores for %d CVEs", len(results))
    return results


def merge_epss_into_cves(
    cves: list[dict[str, Any]],
    epss_data: dict[str, dict[str, Any]],
) -> None:
    """Merge EPSS scores into CVE dicts in-place."""
    for cve in cves:
        epss = epss_data.get(cve["id"], {})
        cve["epss_score"] = epss.get("epss_score")
        cve["epss_percentile"] = epss.get("epss_percentile")
