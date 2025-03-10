import logging
import time
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from functools import reduce
from typing import Any
from typing import cast
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from requests import Session

from cartography.client.core.tx import load
from cartography.client.core.tx import read_list_of_values_tx
from cartography.client.core.tx import read_single_value_tx
from cartography.models.cve.cve import CVESchema
from cartography.models.cve.cve_feed import CVEFeedSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Connect and read timeouts of 120 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
CONNECT_AND_READ_TIMEOUT = (30, 120)
CVE_FEED_ID = "NIST_NVD"
BATCH_SIZE_DAYS = 120
RESULTS_PER_PAGE = 2000
DEFAULT_SLEEP_TIME = 3.0
DELAYED_SLEEP_TIME = 6.0


@timeit
def get_cve_sync_metadata(neo4j_session: neo4j.Session) -> List[int]:
    get_cve_years_query = """
    MATCH (s:SyncMetadata)
    WHERE s.grouptype = "CVE" AND s.syncedtype = "year"
    RETURN s.groupid
    """
    results = read_list_of_values_tx(neo4j_session, get_cve_years_query)
    years = [int(year) for year in results]
    return years


@timeit
def get_last_modified_cve_date(neo4j_session: neo4j.Session) -> str:
    query = """
    MATCH (c:CVE) WHERE c.id STARTS WITH "CVE"
    RETURN DISTINCT datetime(c.last_modified_date) AS last_modified
    ORDER BY last_modified DESC
    LIMIT 1
    """
    result = cast(neo4j.time.DateTime, read_single_value_tx(neo4j_session, query)).to_native()
    return result.strftime("%Y-%m-%dT%H:%M:%S")


def _map_cve_dict(cve_dict: Dict[Any, Any], data: Dict[Any, Any]) -> None:
    cve_dict["format"] = data["format"]
    cve_dict["version"] = data["version"]
    cve_dict["timestamp"] = data["timestamp"]
    cve_dict["totalResults"] = data["totalResults"]
    cve_dict["vulnerabilities"] = cve_dict.get("vulnerabilities", []) + data.get(
        "vulnerabilities", [],
    )
    cve_dict["resultsPerPage"] = data["resultsPerPage"]
    cve_dict["startIndex"] = data["startIndex"]


def _call_cves_api(http_session: Session, url: str, api_key: str | None, params: Dict[str, Any]) -> Dict[Any, Any]:
    total_results = 0
    params["startIndex"] = 0
    params["resultsPerPage"] = RESULTS_PER_PAGE
    headers = {"Content-Type": "application/json"}
    if api_key:
        sleep_between_requests = DEFAULT_SLEEP_TIME
        headers["apiKey"] = api_key
    else:
        sleep_between_requests = DELAYED_SLEEP_TIME
        logger.warning(
            f"No NIST NVD API key provided. Increasing sleep time to {sleep_between_requests}.",
        )
    results: Dict[Any, Any] = dict()

    while params["resultsPerPage"] > 0 or params["startIndex"] < total_results:
        logger.info(f"Calling NIST NVD API at {url} with params {params}")
        res = http_session.get(url, params=params, headers=headers, timeout=CONNECT_AND_READ_TIMEOUT)
        res.raise_for_status()
        data = res.json()
        _map_cve_dict(results, data)
        total_results = data["totalResults"]
        params["resultsPerPage"] = data["resultsPerPage"]
        params["startIndex"] += data["resultsPerPage"]
        time.sleep(sleep_between_requests)
    return results


def get_cves_in_batches(
    http_session: Session,
    nist_cve_url: str,
    start_date: datetime,
    end_date: datetime,
    date_param_names: Dict[str, str],
    api_key: str | None,
) -> Dict[Any, Any]:
    cves: Dict[Any, Any] = dict()
    current_start_date: datetime = start_date
    current_end_date = end_date
    total_days = (current_end_date - current_start_date).days
    batch_size = timedelta(days=BATCH_SIZE_DAYS)
    if total_days < 0:
        raise ValueError(f"Start date {start_date} must be before end date {end_date}.")
    if not date_param_names["start"] or not date_param_names["end"]:
        raise ValueError("Date parameter names 'start' and 'end' must be provided.")
    while current_start_date < end_date:
        remaining = current_end_date - current_start_date
        if remaining > batch_size:
            current_end_date = current_start_date + batch_size
        else:
            current_end_date = (
                end_date if remaining.days == 0 else current_start_date + remaining
            )
        params = {
            date_param_names["start"]: current_start_date.strftime(
                "%Y-%m-%dT%H:%M:%S",
            ),
            date_param_names["end"]: current_end_date.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        logger.info(
            f"Querying CVE data between {current_start_date} and {current_end_date}",
        )
        batch_cves = _call_cves_api(http_session, nist_cve_url, api_key, params)
        _map_cve_dict(cves, batch_cves)
        current_start_date = current_end_date
        new_end_date = current_start_date + batch_size
        if new_end_date > end_date:
            new_end_date = end_date
        current_end_date = new_end_date
    return cves


def get_modified_cves(
    http_session: Session, nist_cve_url: str, last_modified_date: str, api_key: str | None,
) -> Dict[Any, Any]:
    end_date = datetime.now(tz=timezone.utc)
    start_date = datetime.strptime(last_modified_date, "%Y-%m-%dT%H:%M:%S").replace(
        tzinfo=timezone.utc,
    )
    date_param_names = {
        "start": "lastModStartDate",
        "end": "lastModEndDate",
    }
    cves = get_cves_in_batches(
        http_session, nist_cve_url, start_date, end_date, date_param_names, api_key,
    )
    return cves


def get_published_cves_per_year(
    http_session: Session, nist_cve_url: str, year: str, api_key: str | None,
) -> Dict[Any, Any]:
    start_of_year = datetime.strptime(f"{year}-01-01", "%Y-%m-%d")
    next_year = int(year) + 1
    end_of_next_year = datetime.strptime(f"{next_year}-01-01", "%Y-%m-%d")
    date_param_names = {
        "start": "pubStartDate",
        "end": "pubEndDate",
    }
    cves = get_cves_in_batches(
        http_session, nist_cve_url, start_of_year, end_of_next_year, date_param_names, api_key,
    )
    return cves


def _get_primary_metric(metrics: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if metrics is None:
        return metrics
    metric = {}
    for metric in metrics:
        if metric["type"] == "Primary":
            return metric
    return metrics[0]


def transform_cves(cve_json: Dict[Any, Any]) -> List[Dict[Any, Any]]:
    """
    Transform CVE data into a list of dictionaries with only the properties ingested.
    Also, flattens any nested lists and properties to the main object.
    """
    cves = []
    for data in cve_json["vulnerabilities"]:
        try:
            cve = data["cve"]
            cve["descriptions_en"] = [
                description["value"]
                for description in cve.get("descriptions")
                if description["lang"] == "en"
            ]
            cve["references_urls"] = [url["url"] for url in cve["references"]]
            if cve.get("weaknesses"):
                weakness_descriptions = [weakness["description"] for weakness in cve["weaknesses"]]
                weakness_descriptions = reduce(
                    lambda x, y: x + y, weakness_descriptions, [],
                )
                cve["weaknesses"] = [
                    description["value"]
                    for description in weakness_descriptions
                    if description["lang"] == "en"
                ]
            cvss31_metrics = cve.get("metrics", {}).get("cvssMetricV31")
            cvss31 = _get_primary_metric(cvss31_metrics)
            if cvss31:
                cvss31.update(cvss31["cvssData"])
                cvss31.pop("cvssData")
                cve["vectorString"] = cvss31.get("vectorString")
                cve["attackVector"] = cvss31.get("attackVector")
                cve["attackComplexity"] = cvss31.get("attackComplexity")
                cve["privilegesRequired"] = cvss31.get("privilegesRequired")
                cve["userInteraction"] = cvss31.get("userInteraction")
                cve["scope"] = cvss31.get("scope")
                cve["confidentialityImpact"] = cvss31.get("confidentialityImpact")
                cve["integrityImpact"] = cvss31.get("integrityImpact")
                cve["availabilityImpact"] = cvss31.get("availabilityImpact")
                cve["baseScore"] = cvss31.get("baseScore")
                cve["baseSeverity"] = cvss31.get("baseSeverity")
                cve["exploitabilityScore"] = cvss31.get("exploitabilityScore")
                cve["impactScore"] = cvss31.get("impactScore")
        except Exception:
            logger.error("Failed to transform CVE data {data}")
            raise
        cves.append(cve)
    return cves


def transform_cve_feed(cve_json: Dict[Any, Any]) -> Dict[str, str]:
    """
    Extract version, timestamp, and lastupdated from the feed
    """
    feed = {
        "FEED_ID": CVE_FEED_ID,
        "format": cve_json["format"],
        "version": cve_json["version"],
        "timestamp": cve_json["timestamp"],
    }
    return feed


def load_cves(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    feed_id: str,
    update_tag: int,
) -> None:
    """
    Load CVE's information
    """
    logger.info(f"Loading {len(data)} CVEs into the graph.")
    load(
        neo4j_session,
        CVESchema(),
        data,
        lastupdated=update_tag,
        FEED_ID=feed_id,
    )


def load_cve_feed(
    neo4j_session: neo4j.Session, data: List[Dict[str, Any]], update_tag: int,
) -> None:
    """
    Load CVE feed information
    """
    logger.info(f"Loading CVE feed info {data} into the graph...")
    load(
        neo4j_session,
        CVEFeedSchema(),
        data,
        lastupdated=update_tag,
    )
