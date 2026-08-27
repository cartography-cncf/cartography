import logging
from typing import Any

import neo4j

from cartography.config import Config
from cartography.util import timeit
from cartography.util.lazy import lazy_callable
from cartography.util.lazy import lazy_submodule

# Bound lazily so that the provider SDK only loads once the config gate below
# has decided that this module has something to sync.
WorkOSClient = lazy_callable("workos", "WorkOSClient")
sync_api_keys = lazy_callable("cartography.intel.workos.api_keys", "sync")
sync_application_client_secrets = lazy_callable(
    "cartography.intel.workos.application_client_secrets", "sync"
)
sync_applications = lazy_callable("cartography.intel.workos.applications", "sync")
sync_directories = lazy_callable("cartography.intel.workos.directories", "sync")
sync_directory_groups = lazy_callable(
    "cartography.intel.workos.directory_groups", "sync"
)
sync_directory_users = lazy_callable("cartography.intel.workos.directory_users", "sync")
sync_environment = lazy_callable("cartography.intel.workos.environment", "sync")
sync_invitations = lazy_callable("cartography.intel.workos.invitations", "sync")
sync_organization_domains = lazy_callable(
    "cartography.intel.workos.organization_domains", "sync"
)
sync_organization_memberships = lazy_callable(
    "cartography.intel.workos.organization_memberships", "sync"
)
sync_organizations = lazy_callable("cartography.intel.workos.organizations", "sync")
sync_roles = lazy_callable("cartography.intel.workos.roles", "sync")
sync_users = lazy_callable("cartography.intel.workos.users", "sync")

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
    sync_environment(
        neo4j_session,
        common_job_parameters,
    )

    # Sync organizations
    org_ids = sync_organizations(
        neo4j_session,
        client,
        common_job_parameters,
    )

    # Sync organization domains (depends on organization IDs)
    sync_organization_domains(
        neo4j_session,
        client,
        org_ids,
        common_job_parameters,
    )

    # Sync Connect applications
    application_ids = sync_applications(
        neo4j_session,
        client,
        common_job_parameters,
    )

    # Sync Connect application client secrets (depends on application IDs)
    sync_application_client_secrets(
        neo4j_session,
        client,
        application_ids,
        common_job_parameters,
    )

    # Sync API keys (per organization)
    sync_api_keys(
        neo4j_session,
        client,
        org_ids,
        common_job_parameters,
    )

    # Sync users
    sync_users(
        neo4j_session,
        client,
        common_job_parameters,
    )

    # Sync roles (must be before organization memberships)
    sync_roles(
        neo4j_session,
        client,
        org_ids,
        common_job_parameters,
    )

    # Sync organization memberships (links users to organizations and roles)
    sync_organization_memberships(
        neo4j_session,
        client,
        org_ids,
        common_job_parameters,
    )

    # Sync invitations (links to users and organizations)
    sync_invitations(
        neo4j_session,
        client,
        common_job_parameters,
    )

    # Sync directories and get the list of IDs for directory users/groups
    directory_ids = sync_directories(
        neo4j_session,
        client,
        common_job_parameters,
    )

    # Sync directory groups (depends on directory IDs)
    sync_directory_groups(
        neo4j_session,
        client,
        directory_ids,
        common_job_parameters,
    )

    # Sync directory users (depends on directory IDs and directory groups)
    sync_directory_users(
        neo4j_session,
        client,
        directory_ids,
        common_job_parameters,
    )

    logger.info("Completed WorkOS ingestion")


# DEPRECATED: importing this package used to populate its namespace with every
# submodule the entry point pulled, so callers could reach a stage through
# `cartography.intel.workos.<domain>`. Those imports are lazy now, so the names are served on
# demand instead. Remove in v1.0.0.
def __getattr__(name: str) -> Any:
    return lazy_submodule(__name__, name)
