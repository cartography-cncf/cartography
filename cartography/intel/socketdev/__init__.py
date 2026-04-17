import logging

import neo4j

from cartography.config import Config
from cartography.intel.socketdev.alerts import sync_alerts
from cartography.intel.socketdev.dependencies import sync_dependencies
from cartography.intel.socketdev.organizations import sync_organizations
from cartography.intel.socketdev.repositories import sync_repositories
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_socketdev_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
) -> None:
    """
    Main entry point for Socket.dev ingestion.
    Syncs organizations, repositories, dependencies, and security alerts.
    """
    if not config.socketdev_token:
        logger.info(
            "Socket.dev import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    common_job_parameters: dict = {
        "UPDATE_TAG": config.update_tag,
    }

    # sync_organizations must be called first since it populates common_job_parameters
    # with the org ID and slug, which are required by the other sync functions
    sync_organizations(
        neo4j_session,
        config.socketdev_token,
        config.update_tag,
        common_job_parameters,
    )

    org_slug = common_job_parameters.get("ORG_SLUG")
    if not org_slug:
        logger.warning(
            "No Socket.dev organization found. Skipping remaining sync jobs.",
        )
        return

    sync_repositories(
        neo4j_session,
        config.socketdev_token,
        org_slug,
        config.update_tag,
        common_job_parameters,
    )

    sync_dependencies(
        neo4j_session,
        config.socketdev_token,
        org_slug,
        config.update_tag,
        common_job_parameters,
    )

    sync_alerts(
        neo4j_session,
        config.socketdev_token,
        org_slug,
        config.update_tag,
        common_job_parameters,
    )
