import logging
from typing import Any

import neo4j
import scaleway
from scaleway.domain.v2beta1 import DomainSummary
from scaleway.domain.v2beta1 import DomainV2Beta1RegistrarAPI

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.dns.registered_domain import (
    ScalewayRegisteredDomainSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: dict[str, Any],
    org_id: str,
    update_tag: int,
) -> None:
    domains = get(client, org_id)
    formatted_domains = transform_domains(domains)
    load_domains(neo4j_session, formatted_domains, org_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[DomainSummary]:
    api = DomainV2Beta1RegistrarAPI(client)
    # Registered domains are a global (non-regional) resource.
    return api.list_domains_all(organization_id=org_id)


def transform_domains(domains: list[DomainSummary]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for domain in domains:
        formatted = scaleway_obj_to_dict(domain)
        # The domain name is the natural unique id.
        formatted["id"] = formatted["domain"]
        formatted["name"] = formatted["domain"]
        result.append(formatted)
    return result


@timeit
def load_domains(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ScalewayRegisteredDomainSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        ScalewayRegisteredDomainSchema(), common_job_parameters
    ).run(neo4j_session)
