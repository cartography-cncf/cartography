import logging
from collections.abc import Iterable
from collections.abc import Iterator
from dataclasses import dataclass
from dataclasses import field
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.sweet import api
from cartography.intel.sweet.finding_sets import sweet_vulnerability_id
from cartography.intel.sweet.finding_sets import transform_content
from cartography.intel.sweet.finding_sets import vulnerability_ids
from cartography.intel.sweet.finding_sets import WorkloadFindingSets
from cartography.models.sweet.finding_sets import SweetFindingContentSchema
from cartography.models.sweet.finding_sets import SweetFindingSetSchema
from cartography.models.sweet.finding_sets import SweetFindingSetToContentMatchLink
from cartography.models.sweet.finding_sets import SweetWorkloadFindingsSchema
from cartography.models.sweet.vulnerability import SweetVulnerabilitySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Resolved vulnerabilities are not fetched. Cleanup then removes the ones that were
# resolved since the previous sync. The API's status filter is case-sensitive and
# takes the title-case values it returns, so a lowercase filter matches nothing.
ACTIVE_STATUSES = "Open,In Progress,Ignored"

# Sets carry their content IDs and workloads their detections, so writes are bounded
# by detections rather than rows: a few large workloads would otherwise send millions
# of detections in one transaction.
DETECTIONS_PER_WRITE = 10_000


def get(
    session: requests.Session,
    api_url: str,
) -> Iterator[list[dict[str, Any]]]:
    return api.iter_pages(
        session,
        api_url,
        "/v1/vulnerability",
        {"status": ACTIVE_STATUSES},
        "vulnerabilities",
    )


def transform_vulnerability(
    vulnerability: dict[str, Any],
    tenant_id: str,
) -> dict[str, Any] | None:
    vulnerability_id, cve_id = vulnerability_ids(vulnerability.get("cve"))
    if not vulnerability_id:
        return None
    return {
        "id": sweet_vulnerability_id(tenant_id, vulnerability_id),
        "vulnerability_id": vulnerability_id,
        "cve_id": cve_id,
        "has_cve": str(cve_id is not None).lower(),
        "severity": vulnerability.get("severity"),
        "epss_score": vulnerability.get("epssScore"),
        "epss_percentile": vulnerability.get("epssPercentile"),
        "published_date": vulnerability.get("publishedDate"),
    }


@dataclass
class _SyncState:
    finding_sets: WorkloadFindingSets
    loaded_content_ids: set[str] = field(default_factory=set)
    loaded_epss_scores: dict[str, float] = field(default_factory=dict)

    def is_new_or_higher_epss(self, vulnerability: dict[str, Any]) -> bool:
        epss_score = vulnerability["epss_score"]
        score = -1.0 if epss_score is None else epss_score
        loaded = self.loaded_epss_scores.get(vulnerability["id"])
        if loaded is not None and score <= loaded:
            return False
        self.loaded_epss_scores[vulnerability["id"]] = score
        return True


@timeit
def load_vulnerabilities(
    neo4j_session: neo4j.Session,
    vulnerabilities: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SweetVulnerabilitySchema(),
        vulnerabilities,
        lastupdated=update_tag,
        SWEET_TENANT_ID=tenant_id,
    )


@timeit
def load_finding_contents(
    neo4j_session: neo4j.Session,
    contents: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SweetFindingContentSchema(),
        contents,
        lastupdated=update_tag,
        SWEET_TENANT_ID=tenant_id,
    )


@timeit
def load_finding_sets(
    neo4j_session: neo4j.Session,
    finding_sets: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SweetFindingSetSchema(),
        finding_sets,
        lastupdated=update_tag,
        SWEET_TENANT_ID=tenant_id,
    )


@timeit
def load_finding_set_contents(
    neo4j_session: neo4j.Session,
    finding_set_slots: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load_matchlinks(
        neo4j_session,
        SweetFindingSetToContentMatchLink(),
        finding_set_slots,
        lastupdated=update_tag,
        _sub_resource_label="SweetTenant",
        _sub_resource_id=tenant_id,
    )


@timeit
def load_workload_findings(
    neo4j_session: neo4j.Session,
    workload_findings: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SweetWorkloadFindingsSchema(),
        workload_findings,
        lastupdated=update_tag,
        SWEET_TENANT_ID=tenant_id,
    )


def _batches_of_detections(
    rows: Iterable[dict[str, Any]],
    detections_key: str,
) -> Iterator[list[dict[str, Any]]]:
    batch: list[dict[str, Any]] = []
    batch_detections = 0
    for row in rows:
        if batch and batch_detections + len(row[detections_key]) > DETECTIONS_PER_WRITE:
            yield batch
            batch, batch_detections = [], 0
        batch.append(row)
        batch_detections += len(row[detections_key])
    if batch:
        yield batch


def _load_page(
    neo4j_session: neo4j.Session,
    page: list[dict[str, Any]],
    state: _SyncState,
    tenant_id: str,
    update_tag: int,
) -> None:
    vulnerabilities: list[dict[str, Any]] = []
    contents: list[dict[str, Any]] = []
    for raw in page:
        vulnerability = transform_vulnerability(raw, tenant_id)
        if vulnerability and state.is_new_or_higher_epss(vulnerability):
            vulnerabilities.append(vulnerability)
        content = transform_content(raw, tenant_id)
        if content["id"] not in state.loaded_content_ids:
            state.loaded_content_ids.add(content["id"])
            contents.append(content)
        state.finding_sets.add(raw, content["id"])
    # Vulnerabilities go first so that new contents can link to them.
    load_vulnerabilities(neo4j_session, vulnerabilities, tenant_id, update_tag)
    load_finding_contents(neo4j_session, contents, tenant_id, update_tag)


def _load_finding_sets(
    neo4j_session: neo4j.Session,
    state: _SyncState,
    tenant_id: str,
    update_tag: int,
) -> None:
    finding_sets, finding_set_slots, workload_findings = state.finding_sets.build()
    logger.info(
        "Loading %d Sweet finding sets for %d workloads.",
        len(finding_sets),
        len(workload_findings),
    )
    for batch in _batches_of_detections(finding_sets, "content_ids"):
        load_finding_sets(neo4j_session, batch, tenant_id, update_tag)
    load_finding_set_contents(neo4j_session, finding_set_slots, tenant_id, update_tag)
    for batch in _batches_of_detections(workload_findings, "finding_ids"):
        load_workload_findings(neo4j_session, batch, tenant_id, update_tag)


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    # A workload that Sweet stopped reporting takes only its own node with it; its set
    # and contents go once no workload reports them.
    for schema in (
        SweetWorkloadFindingsSchema(),
        SweetFindingSetSchema(),
        SweetFindingContentSchema(),
    ):
        GraphJob.from_node_schema(schema, common_job_parameters).run(neo4j_session)
    GraphJob.from_matchlink(
        SweetFindingSetToContentMatchLink(),
        "SweetTenant",
        common_job_parameters["SWEET_TENANT_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        SweetVulnerabilitySchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    api_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    # A large tenant reports hundreds of millions of detections, mostly the same
    # findings on workloads that run the same images. Vulnerabilities and contents
    # load as each page arrives; workload sets load once every page has, since a
    # workload's detections are spread across pages.
    state = _SyncState(finding_sets=WorkloadFindingSets(tenant_id))
    for page in get(session, api_url):
        _load_page(neo4j_session, page, state, tenant_id, update_tag)
    _load_finding_sets(neo4j_session, state, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
