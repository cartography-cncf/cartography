import logging
from collections.abc import Iterable
from collections.abc import Iterator
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sweet import api
from cartography.models.sweet.attack_chain import SweetAttackChainSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Resolved and Closed chains are not fetched. Cleanup then removes the ones that
# were resolved or closed since the previous sync.
ACTIVE_STATUSES = "Open,In Progress"


def get(
    session: requests.Session,
    api_url: str,
) -> Iterator[list[dict[str, Any]]]:
    return api.iter_pages(
        session,
        api_url,
        "/v1/attack",
        {"status": ACTIVE_STATUSES},
        "attack chains",
    )


def _empty_to_none(value: str | None) -> str | None:
    # Sweet returns "" rather than null for some unresolved string fields.
    return value or None


def _normalize_domain(domain: str | None) -> str | None:
    """Lowercase the host and drop a trailing dot and port, as DNSRecord names are stored."""
    if not domain:
        return None
    host = domain.strip().lower()
    name, separator, port = host.rpartition(":")
    if separator and port.isdigit() and ":" not in name:
        host = name
    return host.rstrip(".") or None


def _format_endpoints(endpoints: list[dict[str, Any]] | None) -> list[str] | None:
    if not endpoints:
        return None
    formatted = [
        " ".join(
            part for part in (endpoint.get("method"), endpoint.get("path")) if part
        )
        for endpoint in endpoints
    ]
    return [endpoint for endpoint in formatted if endpoint] or None


def transform(raw_chains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": chain["id"],
            "title": chain.get("title"),
            "description": chain.get("description"),
            "story": chain.get("story"),
            "severity": chain.get("severity"),
            "status": chain.get("status"),
            "confidence": _empty_to_none(chain.get("confidence")),
            "impact": chain.get("impact"),
            "owasp": chain.get("owasp"),
            "cwe": chain.get("cwe"),
            "domain": _normalize_domain(chain.get("domain")),
            "endpoints": _format_endpoints(chain.get("endpoints")),
            "first_detected_at": chain.get("firstDetectedAt"),
            "last_detected_at": chain.get("lastDetectedAt"),
            "execution_name": _empty_to_none(chain.get("executionName")),
            "campaign_name": _empty_to_none(chain.get("campaignName")),
            "asset_id": chain.get("assetId"),
        }
        for chain in raw_chains
    ]


@timeit
def load_attack_chains(
    neo4j_session: neo4j.Session,
    chains: Iterable[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SweetAttackChainSchema(),
        chains,
        lastupdated=update_tag,
        SWEET_TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SweetAttackChainSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    api_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    load_attack_chains(
        neo4j_session,
        (chain for page in get(session, api_url) for chain in transform(page)),
        tenant_id,
        update_tag,
    )
    cleanup(neo4j_session, common_job_parameters)
