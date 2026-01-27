import logging
from typing import Any

import neo4j
from workos import WorkOSClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.workos.util import paginated_list
from cartography.models.workos.organization_domain import WorkOSOrganizationDomainSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: WorkOSClient,
    organization_ids: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync WorkOS Organization Domains.

    :param neo4j_session: Neo4J session for database interface
    :param client: WorkOS API client
    :param organization_ids: List of organization IDs from organizations.sync()
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    client_id = common_job_parameters["WORKOS_CLIENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    domains = get(client, organization_ids)
    transformed_domains = transform(domains)
    load_organization_domains(neo4j_session, transformed_domains, client_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(client: WorkOSClient, organization_ids: list[str]) -> list[dict[str, Any]]:
    """
    Fetch all organization domains from WorkOS API.

    :param client: WorkOS API client
    :param organization_ids: List of organization IDs
    :return: List of organization domain dicts
    """
    logger.debug("Fetching WorkOS organization domains")
    domains = []

    for org_id in organization_ids:
        try:
            org_domains = paginated_list(
                client.organizations.list_organization_domains,
                organization_id=org_id,
            )
            domains.extend(org_domains)
        except Exception as e:
            logger.warning(f"Failed to fetch domains for organization {org_id}: {e}")
            continue

    return domains


def transform(domains: list[Any]) -> list[dict[str, Any]]:
    """
    Transform organization domains data for loading.

    :param domains: Raw organization domain objects from WorkOS
    :return: Transformed list of organization domain dicts
    """
    logger.debug(f"Transforming {len(domains)} WorkOS organization domains")
    result = []

    for domain in domains:
        domain_dict = {
            "id": domain.id,
            "domain": domain.domain,
            "organization_id": domain.organization_id,
            "state": domain.state,
            "verification_strategy": domain.verification_strategy,
            "verification_token": getattr(domain, "verification_token", None),
        }
        result.append(domain_dict)

    return result


@timeit
def load_organization_domains(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    client_id: str,
    update_tag: int,
) -> None:
    """
    Load organization domains into Neo4j.

    :param neo4j_session: Neo4J session for database interface
    :param data: List of organization domain dicts
    :param client_id: The WorkOS client ID
    :param update_tag: Update tag for tracking syncs
    :return: None
    """
    logger.info(f"Loading {len(data)} WorkOS organization domains into Neo4j")
    load(
        neo4j_session,
        WorkOSOrganizationDomainSchema(),
        data,
        lastupdated=update_tag,
        WORKOS_CLIENT_ID=client_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Cleanup old organization domains.

    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common parameters for cleanup jobs
    :return: None
    """
    GraphJob.from_node_schema(
        WorkOSOrganizationDomainSchema(),
        common_job_parameters,
    ).run(neo4j_session)
