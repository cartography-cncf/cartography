import logging

import neo4j
from workos import WorkOSClient

import cartography.intel.workos.api_keys
import cartography.intel.workos.applications
import cartography.intel.workos.directories
import cartography.intel.workos.directory_groups
import cartography.intel.workos.directory_users
import cartography.intel.workos.environment
import cartography.intel.workos.invitations
import cartography.intel.workos.organization_domains
import cartography.intel.workos.organization_memberships
import cartography.intel.workos.organizations
import cartography.intel.workos.roles
import cartography.intel.workos.users
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_workos_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of WorkOS data. Otherwise warn and exit.

    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.workos_api_key or not config.workos_client_id:
        logger.info(
            "WorkOS import is not configured - skipping this module. "
            "See docs to configure."
        )
        return

    logger.info("Starting WorkOS ingestion")

    # Initialize WorkOS client
    client = WorkOSClient(
        api_key=config.workos_api_key, client_id=config.workos_client_id
    )

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "WORKOS_CLIENT_ID": config.workos_client_id,
    }

    # Sync environment first (local-only, creates root node)
    cartography.intel.workos.environment.sync(
        neo4j_session,
        common_job_parameters,
    )

    # Sync organizations
    org_ids = cartography.intel.workos.organizations.sync(
        neo4j_session,
        client,
        common_job_parameters,
    )

    # Sync organization domains (depends on organization IDs)
    cartography.intel.workos.organization_domains.sync(
        neo4j_session,
        client,
        org_ids,
        common_job_parameters,
    )

    # WIP: Skip until Applications are supported in SDK
    # # Sync applications (OAuth and M2M)
    # cartography.intel.workos.applications.sync(
    #    neo4j_session,
    #    client,
    #    common_job_parameters,
    # )

    # Sync API keys (per organization)
    cartography.intel.workos.api_keys.sync(
        neo4j_session,
        client,
        org_ids,
        common_job_parameters,
    )

    # Sync users
    cartography.intel.workos.users.sync(
        neo4j_session,
        client,
        common_job_parameters,
    )

    # Sync roles (must be before organization memberships)
    cartography.intel.workos.roles.sync(
        neo4j_session,
        client,
        org_ids,
        common_job_parameters,
    )

    # Sync organization memberships (links users to organizations and roles)
    cartography.intel.workos.organization_memberships.sync(
        neo4j_session,
        client,
        org_ids,
        common_job_parameters,
    )

    # Sync invitations (links to users and organizations)
    cartography.intel.workos.invitations.sync(
        neo4j_session,
        client,
        common_job_parameters,
    )

    # Sync directories and get the list of IDs for directory users/groups
    directory_ids = cartography.intel.workos.directories.sync(
        neo4j_session,
        client,
        common_job_parameters,
    )

    # Sync directory groups (depends on directory IDs)
    cartography.intel.workos.directory_groups.sync(
        neo4j_session,
        client,
        directory_ids,
        common_job_parameters,
    )

    # Sync directory users (depends on directory IDs and directory groups)
    cartography.intel.workos.directory_users.sync(
        neo4j_session,
        client,
        directory_ids,
        common_job_parameters,
    )

    logger.info("Completed WorkOS ingestion")
