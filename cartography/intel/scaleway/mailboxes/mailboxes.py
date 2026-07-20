import logging
from typing import Any

import neo4j
import scaleway
from scaleway.mailbox.v1alpha1 import Domain
from scaleway.mailbox.v1alpha1 import Mailbox
from scaleway.mailbox.v1alpha1 import MailboxV1Alpha1API

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.mailbox.domain import ScalewayMailboxDomainSchema
from cartography.models.scaleway.mailbox.mailbox import ScalewayMailboxSchema
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
    domains, mailboxes = get(client, projects_id)
    domains_by_project, mailboxes_by_project = transform(domains, mailboxes)
    load_mailbox_domains(neo4j_session, domains_by_project, update_tag)
    load_mailboxes(neo4j_session, mailboxes_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    projects_id: list[str],
) -> tuple[list[Domain], list[Mailbox]]:
    api = MailboxV1Alpha1API(client)
    domains: list[Domain] = []
    for project_id in projects_id:
        domains.extend(api.list_domains_all(project_id=project_id))
    mailboxes: list[Mailbox] = [
        mailbox
        for domain in domains
        for mailbox in api.list_mailboxes_all(domain_id=domain.id)
    ]
    return domains, mailboxes


def transform(
    domains: list[Domain],
    mailboxes: list[Mailbox],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    domains_by_project: dict[str, list[dict[str, Any]]] = {}
    project_by_domain_id: dict[str, str] = {}
    for domain in domains:
        formatted_domain = scaleway_obj_to_dict(domain)
        domains_by_project.setdefault(domain.project_id, []).append(formatted_domain)
        project_by_domain_id[domain.id] = domain.project_id

    mailboxes_by_project: dict[str, list[dict[str, Any]]] = {}
    for mailbox in mailboxes:
        project_id = project_by_domain_id.get(mailbox.domain_id)
        if project_id is None:
            logger.warning(
                "Skipping Scaleway Mailbox %s: unknown parent domain %s.",
                mailbox.id,
                mailbox.domain_id,
            )
            continue
        formatted_mailbox = scaleway_obj_to_dict(mailbox)
        formatted_mailbox["project_id"] = project_id
        mailboxes_by_project.setdefault(project_id, []).append(formatted_mailbox)

    return domains_by_project, mailboxes_by_project


@timeit
def load_mailbox_domains(
    neo4j_session: neo4j.Session,
    data: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, domains in data.items():
        logger.info(
            "Loading %d Scaleway Mailbox domains in project '%s' into Neo4j.",
            len(domains),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayMailboxDomainSchema(),
            domains,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )


@timeit
def load_mailboxes(
    neo4j_session: neo4j.Session,
    data: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, mailboxes in data.items():
        logger.info(
            "Loading %d Scaleway Mailboxes in project '%s' into Neo4j.",
            len(mailboxes),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayMailboxSchema(),
            mailboxes,
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
        # Mailboxes before domains: a stale domain's child mailboxes must be
        # cleaned up before the domain itself, otherwise they'd be orphaned
        # for one sync cycle.
        GraphJob.from_node_schema(ScalewayMailboxSchema(), scoped_job_parameters).run(
            neo4j_session
        )
        GraphJob.from_node_schema(
            ScalewayMailboxDomainSchema(), scoped_job_parameters
        ).run(neo4j_session)
