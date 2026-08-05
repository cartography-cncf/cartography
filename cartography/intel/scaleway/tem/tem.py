import logging
from typing import Any

import neo4j
import scaleway
from scaleway.tem.v1alpha1 import Domain
from scaleway.tem.v1alpha1 import TemV1Alpha1API

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.tem.tem import ScalewayTemDomainSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: dict[str, Any],
    org_id: str,
    projects_id: list[str],
    update_tag: int,
) -> None:
    domains = get(client, org_id)
    domains_by_project = transform_domains(domains)
    load_domains(neo4j_session, domains_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> list[Domain]:
    api = TemV1Alpha1API(client)
    return api.list_domains_all(organization_id=org_id)


def transform_domains(
    domains: list[Domain],
) -> dict[str, list[dict[str, Any]]]:
    domains_by_project: dict[str, list[dict[str, Any]]] = {}
    for domain in domains:
        formatted = scaleway_obj_to_dict(domain)
        project_id = getattr(domain, "project_id", None)
        if project_id is None:
            logger.warning(
                "Skipping Scaleway TEM domain %s: missing project_id.",
                domain.id,
            )
            continue
        domains_by_project.setdefault(project_id, []).append(formatted)
    return domains_by_project


@timeit
def load_domains(
    neo4j_session: neo4j.Session,
    domains_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, domains in domains_by_project.items():
        logger.info(
            "Loading %d Scaleway TEM domains in project '%s' into Neo4j.",
            len(domains),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayTemDomainSchema(),
            domains,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    projects_id: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    for project_id in projects_id:
        scoped_job_parameters = common_job_parameters.copy()
        scoped_job_parameters["PROJECT_ID"] = project_id
        GraphJob.from_node_schema(ScalewayTemDomainSchema(), scoped_job_parameters).run(
            neo4j_session
        )
