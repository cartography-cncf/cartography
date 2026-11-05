import logging

import neo4j

import cartography.intel.neon.branches
import cartography.intel.neon.databases
import cartography.intel.neon.endpoints
import cartography.intel.neon.organizations
import cartography.intel.neon.projects
import cartography.intel.neon.storage
from cartography.config import Config
from cartography.intel.neon.util import build_session
from cartography.util import timeit

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://console.neon.tech/api/v2"


@timeit
def start_neon_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Neon data. Otherwise warn
    and exit.

    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.neon_api_key:
        logger.info(
            "Neon import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    api_session = build_session(config.neon_api_key)
    base_url = (config.neon_base_url or DEFAULT_BASE_URL).rstrip("/")

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "BASE_URL": base_url,
    }

    org_ids = None
    if config.neon_org_ids:
        org_ids = [o.strip() for o in config.neon_org_ids.split(",") if o.strip()]

    organizations = cartography.intel.neon.organizations.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        org_ids,
    )

    for organization in organizations:
        org_id = organization["id"]
        common_job_parameters["ORG_ID"] = org_id
        cartography.intel.neon.organizations.sync_members(
            neo4j_session,
            api_session,
            common_job_parameters,
        )

        projects, projects_complete = cartography.intel.neon.projects.get(
            api_session,
            base_url,
            org_id,
        )
        cartography.intel.neon.projects.sync(
            neo4j_session,
            projects,
            common_job_parameters,
        )

        for project in projects:
            common_job_parameters["PROJECT_ID"] = project["id"]
            branches = cartography.intel.neon.branches.sync(
                neo4j_session,
                api_session,
                common_job_parameters,
            )
            endpoints = cartography.intel.neon.endpoints.sync(
                neo4j_session,
                api_session,
                project,
                branches,
                common_job_parameters,
            )
            cartography.intel.neon.databases.sync(
                neo4j_session,
                api_session,
                project,
                branches,
                endpoints,
                common_job_parameters,
            )
            cartography.intel.neon.storage.sync(
                neo4j_session,
                api_session,
                branches,
                common_job_parameters,
            )
        common_job_parameters.pop("PROJECT_ID", None)

        # After projects and members, so SCOPED_TO and OWNED_BY can attach.
        cartography.intel.neon.organizations.sync_api_keys(
            neo4j_session,
            api_session,
            common_job_parameters,
        )

        # Remove projects deleted upstream only now that every surviving
        # project's children have been synced. The cascade takes their children
        # with them. A listing with unavailable projects must not drive it: those
        # projects still exist, and the cascade would wipe their whole subtree.
        if projects_complete:
            cartography.intel.neon.projects.cleanup(
                neo4j_session,
                common_job_parameters,
            )
        else:
            logger.warning(
                "Neon project listing for organization %s was incomplete - "
                "skipping project cleanup.",
                org_id,
            )
