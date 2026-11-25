import logging
import re
from collections.abc import Iterable
from collections.abc import Iterator
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sweet import api
from cartography.models.sweet.vulnerability import SweetVulnerabilitySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Resolved vulnerabilities are not fetched. Cleanup then removes the ones that were
# resolved since the previous sync. The API's status filter is case-sensitive and
# takes the title-case values it returns, so a lowercase filter matches nothing.
ACTIVE_STATUSES = "Open,In Progress,Ignored"
_BARE_SHA256 = re.compile(r"^[0-9a-f]{64}$")


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


def _normalize_status(status: str | None) -> str | None:
    """Turn Sweet's title-case status, such as `In Progress`, into `in_progress`."""
    if not status:
        return None
    return "_".join(status.strip().lower().split()) or None


def _image_digest_for_match(digest: str | None) -> str | None:
    """Return the digest in the `sha256:<hex>` form that `Image._ont_digest` uses."""
    if not digest:
        return None
    normalized = digest.strip().lower()
    if normalized.startswith("sha256:"):
        return normalized
    if _BARE_SHA256.match(normalized):
        return f"sha256:{normalized}"
    return None


def transform(raw_vulnerabilities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for vulnerability in raw_vulnerabilities:
        vulnerability_id = vulnerability.get("cve")
        cve_id = (
            vulnerability_id.upper()
            if vulnerability_id and vulnerability_id.upper().startswith("CVE-")
            else None
        )
        package = vulnerability.get("package") or {}
        image = vulnerability.get("image") or {}
        code_owner = vulnerability.get("codeOwner") or {}
        result.append(
            {
                "id": vulnerability["id"],
                "vulnerability_id": vulnerability_id,
                "cve_id": cve_id,
                "has_cve": str(cve_id is not None).lower(),
                "severity": vulnerability.get("severity"),
                "status": _normalize_status(vulnerability.get("status")),
                "sweet_score": vulnerability.get("sweetScore"),
                "sweet_severity": vulnerability.get("sweetSeverity"),
                "epss_score": vulnerability.get("epssScore"),
                "epss_percentile": vulnerability.get("epssPercentile"),
                "risk_indicators": vulnerability.get("riskIndicators"),
                "attack_labels": vulnerability.get("attackLabels"),
                "published_date": vulnerability.get("publishedDate"),
                "first_detected": vulnerability.get("firstDetected"),
                "last_detected": vulnerability.get("lastDetected"),
                "last_loaded": vulnerability.get("lastLoaded"),
                "last_executed": vulnerability.get("lastExecuted"),
                "has_fix": vulnerability.get("hasFix"),
                "fixed_in_versions": vulnerability.get("fixedInVersions"),
                "package_name": package.get("name"),
                "package_version": package.get("version"),
                "package_manager": package.get("manager"),
                "image_name": image.get("name"),
                "image_tag": image.get("tag"),
                "image_digest": image.get("digest"),
                "image_registry": image.get("registry"),
                "affected_image_digest": _image_digest_for_match(image.get("digest")),
                "workload": vulnerability.get("workload"),
                "cloud_account": vulnerability.get("cloudAccount"),
                "code_owner_name": code_owner.get("name"),
                "code_owner_email": code_owner.get("email"),
            },
        )
    return result


@timeit
def load_vulnerabilities(
    neo4j_session: neo4j.Session,
    vulnerabilities: Iterable[dict[str, Any]],
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
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
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
    # A large tenant has hundreds of thousands of active vulnerabilities, so each
    # page is transformed as it arrives and load batches them, instead of holding
    # every raw and transformed record at once.
    load_vulnerabilities(
        neo4j_session,
        (
            vulnerability
            for page in get(session, api_url)
            for vulnerability in transform(page)
        ),
        tenant_id,
        update_tag,
    )
    cleanup(neo4j_session, common_job_parameters)
