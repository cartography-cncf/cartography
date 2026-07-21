import logging
from typing import Any

import neo4j
import scaleway
from scaleway.mailbox.v1alpha1 import Domain
from scaleway.mailbox.v1alpha1 import Mailbox
from scaleway.mailbox.v1alpha1 import MailboxV1Alpha1API
from scaleway_core.api import ScalewayException

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
    # Only clean up projects we could actually read. Mailbox is private beta;
    # a project without entitlement is skipped entirely, so its previously
    # ingested nodes (if any) are not wiped by a cleanup that saw zero
    # domains/mailboxes.
    fetched_projects: list[str] = []
    for project_id in projects_id:
        result = get(client, project_id)
        if result is None:
            continue
        domains, mailboxes = result
        formatted_domains, formatted_mailboxes = transform(domains, mailboxes)
        load_mailbox_domains(neo4j_session, project_id, formatted_domains, update_tag)
        load_mailboxes(neo4j_session, project_id, formatted_mailboxes, update_tag)
        fetched_projects.append(project_id)
    cleanup(neo4j_session, fetched_projects, common_job_parameters)


@timeit
def get(
    client: scaleway.Client,
    project_id: str,
) -> tuple[list[Domain], list[Mailbox]] | None:
    """Return the project's Mailbox domains and mailboxes, or None if the
    project cannot be read. None signals the caller to skip load/cleanup for
    that project rather than treating the error as an authoritative empty
    set."""
    api = MailboxV1Alpha1API(client)
    try:
        domains = api.list_domains_all(project_id=project_id)
        mailboxes = [
            mailbox
            for domain in domains
            for mailbox in api.list_mailboxes_all(domain_id=domain.id)
        ]
        return domains, mailboxes
    except ScalewayException as exc:
        # Mailbox is a private beta product; accounts without entitlement
        # answer 403 for the whole API. Skip rather than aborting the sync or
        # wiping existing inventory.
        if exc.status_code == 403:
            logger.info(
                "Scaleway Mailbox not enabled for project %s, skipping.",
                project_id,
            )
            return None
        raise


def transform(
    domains: list[Domain],
    mailboxes: list[Mailbox],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    formatted_domains = [scaleway_obj_to_dict(domain) for domain in domains]
    formatted_mailboxes = [scaleway_obj_to_dict(mailbox) for mailbox in mailboxes]
    return formatted_domains, formatted_mailboxes


@timeit
def load_mailbox_domains(
    neo4j_session: neo4j.Session,
    project_id: str,
    domains: list[dict[str, Any]],
    update_tag: int,
) -> None:
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
    project_id: str,
    mailboxes: list[dict[str, Any]],
    update_tag: int,
) -> None:
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
