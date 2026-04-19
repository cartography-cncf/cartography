import logging

import neo4j

from cartography.config import Config
from cartography.intel.socketdev.alerts import sync_alerts
from cartography.intel.socketdev.dependencies import sync_dependencies
from cartography.intel.socketdev.fixes import sync_fixes
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
    Syncs organizations, repositories, dependencies, security alerts, and fixes.
    Iterates over all organizations found in the account.
    """
    if not config.socketdev_token:
        logger.info(
            "Socket.dev import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    organizations = sync_organizations(
        neo4j_session,
        config.socketdev_token,
        config.update_tag,
    )

    if not organizations:
        logger.warning(
            "No Socket.dev organizations found. Skipping remaining sync jobs.",
        )
        return

    # The dependencies search endpoint (POST /dependencies/search) is not
    # org-scoped — it returns all dependencies visible to the API token.
    # We sync it once and attach to the first organization to avoid
    # duplicating the same dependency set across multiple orgs.
    first_org = organizations[0]
    dep_job_parameters: dict = {
        "UPDATE_TAG": config.update_tag,
        "ORG_ID": first_org["id"],
        "ORG_SLUG": first_org["slug"],
    }
    all_dependencies = sync_dependencies(
        neo4j_session,
        config.socketdev_token,
        config.update_tag,
        dep_job_parameters,
    )

    for org in organizations:
        org_id = org["id"]
        org_slug = org["slug"]

        common_job_parameters: dict = {
            "UPDATE_TAG": config.update_tag,
            "ORG_ID": org_id,
            "ORG_SLUG": org_slug,
        }

        logger.info("Syncing Socket.dev data for org '%s'", org_slug)

        sync_repositories(
            neo4j_session,
            config.socketdev_token,
            org_slug,
            config.update_tag,
            common_job_parameters,
        )

        org_alerts = sync_alerts(
            neo4j_session,
            config.socketdev_token,
            org_slug,
            config.update_tag,
            common_job_parameters,
        )

        sync_fixes(
            neo4j_session,
            config.socketdev_token,
            org_slug,
            config.update_tag,
            common_job_parameters,
            alerts=org_alerts,
            dependencies=all_dependencies,
        )
