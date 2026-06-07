import logging

import neo4j
import requests

import cartography.intel.sentry.alertrules
import cartography.intel.sentry.members
import cartography.intel.sentry.organizations
import cartography.intel.sentry.projects
import cartography.intel.sentry.releases
import cartography.intel.sentry.teams
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_sentry_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Sentry data. Otherwise warn and exit.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.sentry_token:
        logger.info(
            "Sentry import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    if not config.sentry_org:
        logger.warning(
            "Sentry token is configured but --sentry-org is not set. "
            "Internal integration tokens require --sentry-org to work correctly.",
        )

    base_url = f"{config.sentry_host.rstrip('/')}/api/0"

    api_session = requests.Session()
    api_session.headers.update(
        {"Authorization": f"Bearer {config.sentry_token}"},
    )

    # 1. Sync organizations
    orgs = cartography.intel.sentry.organizations.sync(
        neo4j_session,
        api_session,
        config.update_tag,
        base_url,
        org_slug=config.sentry_org,
    )

    for org in orgs:
        org_id = org["id"]
        org_slug = org["slug"]

        common_job_parameters = {
            "UPDATE_TAG": config.update_tag,
            "ORG_ID": org_id,
        }

        # 2. Sync teams
        teams = cartography.intel.sentry.teams.sync(
            neo4j_session,
            api_session,
            org_id,
            org_slug,
            config.update_tag,
            common_job_parameters,
            base_url,
        )

        # 3. Sync members (needs teams for team_ids resolution)
        cartography.intel.sentry.members.sync(
            neo4j_session,
            api_session,
            org_id,
            org_slug,
            config.update_tag,
            common_job_parameters,
            base_url,
            teams,
        )

        # 4. Sync projects
        projects = cartography.intel.sentry.projects.sync(
            neo4j_session,
            api_session,
            org_id,
            org_slug,
            config.update_tag,
            common_job_parameters,
            base_url,
        )

        # 5. Sync releases
        cartography.intel.sentry.releases.sync(
            neo4j_session,
            api_session,
            org_id,
            org_slug,
            config.update_tag,
            common_job_parameters,
            base_url,
        )

        # 6. Sync alert rules (per project, cleanup at org level)
        for project in projects:
            cartography.intel.sentry.alertrules.sync(
                neo4j_session,
                api_session,
                org_id,
                org_slug,
                project,
                config.update_tag,
                base_url,
            )
        cartography.intel.sentry.alertrules.cleanup(
            neo4j_session,
            common_job_parameters,
        )
