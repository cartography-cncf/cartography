import logging

import neo4j

from cartography.config import Config
from cartography.util import timeit
from cartography.util.lazy import lazy_callable

# Bound lazily so that the provider SDK only loads once the config gate below
# has decided that this module has something to sync.
sync_alerts = lazy_callable("cartography.intel.socketdev.alerts", "sync_alerts")
sync_dependencies = lazy_callable(
    "cartography.intel.socketdev.dependencies", "sync_dependencies"
)
sync_fixes = lazy_callable("cartography.intel.socketdev.fixes", "sync_fixes")
sync_organizations = lazy_callable(
    "cartography.intel.socketdev.organizations", "sync_organizations"
)
sync_repositories = lazy_callable(
    "cartography.intel.socketdev.repositories", "sync_repositories"
)

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
