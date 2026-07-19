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
    mailboxes_by_project = transform_mailboxes(domains, mailboxes)
    load_mailboxes(neo4j_session, mailboxes_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    projects_id: list[str],
) -> tuple[list[Domain], list[Mailbox]]:
    api = MailboxV1Alpha1API(client)
    domains = [
        domain
        for project_id in projects_id
        for domain in api.list_domains_all(project_id=project_id)
    ]
    mailboxes = [
        mailbox
        for domain in domains
        for mailbox in api.list_mailboxes_all(domain_id=domain.id)
    ]
    return domains, mailboxes


def transform_mailboxes(
    domains: list[Domain],
    mailboxes: list[Mailbox],
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    project_by_domain_id = {domain.id: domain.project_id for domain in domains}
    mailboxes_with_project = [
        (mailbox, project_by_domain_id[mailbox.domain_id])
        for mailbox in mailboxes
        if mailbox.domain_id in project_by_domain_id
    ]

    for mailbox in mailboxes:
        if mailbox.domain_id not in project_by_domain_id:
            logger.warning(
                "Skipping Scaleway Mailbox %s: unknown parent domain %s.",
                mailbox.id,
                mailbox.domain_id,
            )

    for mailbox, project_id in mailboxes_with_project:
        formatted_mailbox = scaleway_obj_to_dict(mailbox)
        formatted_mailbox["project_id"] = project_id
        result.setdefault(project_id, []).append(formatted_mailbox)
    return result


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
        GraphJob.from_node_schema(ScalewayMailboxSchema(), scoped_job_parameters).run(
            neo4j_session
        )
