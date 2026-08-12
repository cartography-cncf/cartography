import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.render.util import BASE_URL
from cartography.intel.render.util import list_paginated
from cartography.intel.render.util import require_non_empty
from cartography.models.render.customdomain import RenderCustomDomainSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, service_id: str) -> list[dict[str, Any]]:
    return list_paginated(
        session,
        f"{BASE_URL}/services/{service_id}/custom-domains",
        "customDomain",
    )


def transform(
    custom_domains: list[dict[str, Any]],
    service_id: str,
    owner_id: str,
) -> list[dict[str, Any]]:
    return [
        {
            "id": require_non_empty(domain.get("id"), "custom domain id"),
            "name": domain.get("name"),
            "ownerId": owner_id,
            "serviceId": service_id,
            "domainType": domain.get("domainType"),
            "publicSuffix": domain.get("publicSuffix"),
            "redirectForName": domain.get("redirectForName"),
            "verificationStatus": domain.get("verificationStatus"),
            "createdAt": domain.get("createdAt"),
        }
        for domain in custom_domains
    ]


@timeit
def load_custom_domains(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    owner_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RenderCustomDomainSchema(),
        data,
        lastupdated=update_tag,
        OWNER_ID=owner_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RenderCustomDomainSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    owner_id: str,
    service_ids: list[str],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    all_domains: list[dict[str, Any]] = []
    for service_id in service_ids:
        domains = get(session, service_id)
        all_domains.extend(transform(domains, service_id, owner_id))
    load_custom_domains(neo4j_session, all_domains, owner_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
