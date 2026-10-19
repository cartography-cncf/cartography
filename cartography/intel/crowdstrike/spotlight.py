import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from typing import Iterable
from typing import Iterator
from typing import TypeVar

import neo4j
from falconpy.oauth2 import OAuth2
from falconpy.spotlight_vulnerabilities import Spotlight_Vulnerabilities

from cartography.client.core.tx import load
from cartography.intel.crowdstrike.util import call_with_retries
from cartography.intel.crowdstrike.util import CrowdstrikeAPIError
from cartography.intel.crowdstrike.util import CrowdstrikeForbiddenError
from cartography.intel.crowdstrike.util import REQUEST_TIMEOUT_SECONDS
from cartography.models.crowdstrike.spotlight import CrowdstrikeCVESchema
from cartography.models.crowdstrike.spotlight import SpotlightVulnerabilitySchema
from cartography.models.crowdstrike.tenant import CrowdstrikeTenantSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
T = TypeVar("T")

SPOTLIGHT_FILTER = 'status:["open","reopen"]'
SPOTLIGHT_SORT = "updated_timestamp|asc"
SPOTLIGHT_PAGE_SIZE = 5000
# combinedQueryVulnerabilities answers an `after` cursor whose search context has
# expired with HTTP 404 ("Search context expired, 'after' key no longer valid").
EXPIRED_CURSOR_STATUS = 404
SPOTLIGHT_FACETS = ["cve", "host_info", "remediation"]


@timeit
def sync_vulnerabilities(
    neo4j_session: neo4j.Session,
    update_tag: int,
    authorization: OAuth2,
) -> bool:
    """
    Sync Spotlight vulnerabilities, returning False if Spotlight was not readable.

    Spotlight is a separately licensed Falcon module. A tenant without it cannot
    grant the Vulnerabilities: Read scope, and its hosts should still sync. The
    caller skips the vulnerability cleanup on False, so losing the scope keeps
    the last synced vulnerabilities rather than deleting them.
    """
    client = Spotlight_Vulnerabilities(
        auth_object=authorization,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    try:
        for vulnerability_data in _prefetch(get_spotlight_vulnerabilities(client)):
            vulns, cves = transform(vulnerability_data)
            load_vulnerability_data(neo4j_session, vulns, update_tag)
            load_cve_data(neo4j_session, cves, update_tag)
    except CrowdstrikeForbiddenError as e:
        logger.warning(
            "Skipping CrowdStrike Spotlight vulnerabilities: %s. Grant the API "
            "client Vulnerabilities: Read to sync them; tenants without the "
            "Spotlight module cannot.",
            e,
        )
        return False
    return True


def _prefetch(pages: Iterable[T]) -> Iterator[T]:
    """
    Fetch the next page while the caller loads the current one.

    Each Spotlight page costs several seconds of API time, so overlapping it with
    the Neo4j load keeps a tens-of-millions sync inside a daily schedule. At most
    two pages are held in memory.
    """
    page_iterator = iter(pages)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(next, page_iterator, None)
        while (page := future.result()) is not None:
            future = executor.submit(next, page_iterator, None)
            yield page


def transform(data: list[dict]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    vulns: list[dict[str, Any]] = []
    cves: list[dict[str, Any]] = []
    for item in data:
        vuln: dict[str, Any] = {}
        for key in [
            "id",
            "aid",
            "cid",
            "status",
            "created_timestamp",
            "closed_timestamp",
            "updated_timestamp",
        ]:
            vuln[key] = item.get(key)
        vuln["remediation_ids"] = _remediation_ids(item)
        vuln["app_product_name_version"] = _app(item).get("product_name_version")
        cve = item.get("cve", {})
        vuln["cve_id"] = cve.get("id")
        if cve:
            cve["vuln_id"] = vuln["id"]
            cves.append(cve)
        vuln["host_info_local_ip"] = item.get("host_info", {}).get("local_ip")
        vulns.append(vuln)
    return vulns, cves


def _remediation_ids(item: dict[str, Any]) -> list[str]:
    # combinedQueryVulnerabilities returns the remediation entities without the
    # `ids` shortcut that getVulnerabilities adds.
    remediation = item.get("remediation") or {}
    if "ids" in remediation:
        return remediation["ids"]
    return [entity["id"] for entity in remediation.get("entities") or []]


def _app(item: dict[str, Any]) -> dict[str, Any]:
    # combinedQueryVulnerabilities has no `app` facet; the affected app is the
    # first entry of `apps`, which is what getVulnerabilities reports as `app`.
    if item.get("app"):
        return item["app"]
    apps = item.get("apps") or []
    return apps[0] if apps else {}


def load_vulnerability_data(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load Spotlight vulnerability data into Neo4j, grouped by CID so each batch
    is scoped to its tenant.
    """
    vulns_by_cid: dict[str, list[dict[str, Any]]] = defaultdict(list)
    missing_cid: list[str] = []
    for vuln in data:
        cid = vuln.get("cid")
        if not cid:
            missing_cid.append(vuln.get("id") or "<unknown>")
            continue
        vulns_by_cid[cid].append(vuln)
    if missing_cid:
        raise ValueError(
            "CrowdStrike returned Spotlight vulnerability records with no `cid`; "
            "refusing to load because the tenant scope cannot be resolved. "
            f"Affected ids: {missing_cid}"
        )
    if not vulns_by_cid:
        return
    load(
        neo4j_session,
        CrowdstrikeTenantSchema(),
        [{"id": cid} for cid in vulns_by_cid],
        lastupdated=update_tag,
    )
    for cid, vulns in vulns_by_cid.items():
        load(
            neo4j_session,
            SpotlightVulnerabilitySchema(),
            vulns,
            lastupdated=update_tag,
            CID=cid,
        )


def load_cve_data(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CrowdstrikeCVESchema(),
        data,
        lastupdated=update_tag,
    )


def get_spotlight_vulnerabilities(
    client: Spotlight_Vulnerabilities,
) -> Iterator[list[dict]]:
    """
    Yield open and reopened vulnerabilities one page at a time.

    A tenant can have tens of millions of these, so the caller loads each page
    before the next one is fetched. The combined endpoint returns 5,000 full
    records per call; querying IDs then fetching details caps at 400 per two
    calls, which made a large tenant's sync take days. Expired vulnerabilities
    are excluded because Spotlight no longer evaluates them.

    The `after` cursor expires while the caller is still loading a page, which a
    busy Neo4j makes routine at this size. Pages are sorted by `updated_timestamp`,
    so an expired cursor restarts the query from the last timestamp yielded rather
    than failing the sync. The restart reads the records sharing that timestamp
    again, which loading tolerates, and an update only moves a record later, so no
    unread record can fall behind the restart point.
    """
    parameters: dict[str, Any] = {
        "filter": SPOTLIGHT_FILTER,
        "sort": SPOTLIGHT_SORT,
        "limit": SPOTLIGHT_PAGE_SIZE,
        "facet": SPOTLIGHT_FACETS,
    }
    seen_cursors: set[str] = set()
    first_page = True
    watermark: str | None = None
    resumed_from: str | None = None
    while True:
        try:
            body = call_with_retries(
                lambda: client.combinedQueryVulnerabilities(parameters=parameters),
                "combinedQueryVulnerabilities",
            )
        except CrowdstrikeAPIError as e:
            if e.status_code != EXPIRED_CURSOR_STATUS or "after" not in parameters:
                raise
            # A restart that expires again before passing its own timestamp would
            # restart there forever.
            if watermark is None or watermark == resumed_from:
                raise CrowdstrikeAPIError(
                    "CrowdStrike combinedQueryVulnerabilities cursor expired again "
                    f"before paging past updated_timestamp {watermark}; refusing to "
                    "restart forever.",
                    status_code=e.status_code,
                ) from e
            logger.warning(
                "CrowdStrike Spotlight pagination cursor expired; restarting from "
                "updated_timestamp %s.",
                watermark,
            )
            resumed_from = watermark
            del parameters["after"]
            parameters["filter"] = (
                f"{SPOTLIGHT_FILTER}+updated_timestamp:>='{watermark}'"
            )
            continue
        resources = body.get("resources") or []
        if not resources:
            if first_page:
                logger.warning(
                    "No vulnerabilities in spotlight combinedQueryVulnerabilities."
                )
            return
        first_page = False
        watermark = resources[-1].get("updated_timestamp") or watermark
        yield resources
        after = body.get("meta", {}).get("pagination", {}).get("after")
        if not after:
            return
        if after in seen_cursors:
            raise CrowdstrikeAPIError(
                "CrowdStrike combinedQueryVulnerabilities returned a pagination cursor "
                "it already returned; refusing to page forever.",
            )
        seen_cursors.add(after)
        parameters["after"] = after
