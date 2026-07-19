import logging
from typing import Any

import neo4j
import scaleway
from scaleway.mailbox.v1alpha1 import Domain
from scaleway.mailbox.v1alpha1 import MailboxV1Alpha1API

from cartography.client.core.tx import load
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.mailbox.domain import ScalewayMailboxDomainSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: dict[str, Any],
    projects_id: list[str],
    update_tag: int,
) -> None:
    domains = get(client, projects_id)
    domains_by_project = transform_domains(domains)
    load_domains(neo4j_session, domains_by_project, update_tag)


@timeit
def get(
    client: scaleway.Client,
    projects_id: list[str],
) -> list[Domain]:
    api = MailboxV1Alpha1API(client)
    domains: list[Domain] = []
    for project_id in projects_id:
        domains.extend(api.list_domains_all(project_id=project_id))
    return domains


@timeit
def transform_domains(
    domains: list[Domain],
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for domain in domains:
        formatted_domain = scaleway_obj_to_dict(domain)
        result.setdefault(domain.project_id, []).append(formatted_domain)
    return result


@timeit
def load_domains(
    neo4j_session: neo4j.Session,
    data: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, domains in data.items():
        load(
            neo4j_session,
            ScalewayMailboxDomainSchema(),
            domains,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )
