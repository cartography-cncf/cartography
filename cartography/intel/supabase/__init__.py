import logging
from collections import defaultdict
from typing import Any

import neo4j

import cartography.intel.supabase.advisors
import cartography.intel.supabase.apikeys
import cartography.intel.supabase.auth
import cartography.intel.supabase.branches
import cartography.intel.supabase.functions
import cartography.intel.supabase.network
import cartography.intel.supabase.organizations
import cartography.intel.supabase.projects
import cartography.intel.supabase.storage
from cartography.config import Config
from cartography.intel.supabase.util import build_session
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_supabase_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Supabase data. Otherwise warn
    and exit.

    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.supabase_access_token:
        logger.info(
            "Supabase import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    api_session = build_session(config.supabase_access_token)

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "BASE_URL": config.supabase_base_url,
    }

    org_allowlist = None
    if config.supabase_organizations:
        org_allowlist = [
            slug.strip()
            for slug in config.supabase_organizations.split(",")
            if slug.strip()
        ]

    organizations = cartography.intel.supabase.organizations.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        org_allowlist,
    )

    # GET /v1/projects is global rather than organization-scoped, so fetch it once
    # and group by organization instead of re-requesting it per organization.
    all_projects = cartography.intel.supabase.projects.get(
        api_session,
        config.supabase_base_url,
    )
    projects_by_org: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for project in all_projects:
        projects_by_org[project["organization_slug"]].append(project)

    for organization in organizations:
        common_job_parameters["ORG_SLUG"] = organization["slug"]
        cartography.intel.supabase.organizations.sync_members(
            neo4j_session,
            api_session,
            common_job_parameters,
        )

        projects = projects_by_org[organization["slug"]]
        cartography.intel.supabase.projects.sync(
            neo4j_session,
            api_session,
            common_job_parameters,
            projects,
        )

        for project in projects:
            common_job_parameters["PROJECT_REF"] = project["ref"]
            cartography.intel.supabase.projects.sync_database(
                neo4j_session,
                api_session,
                project,
                common_job_parameters,
            )
            cartography.intel.supabase.apikeys.sync(
                neo4j_session,
                api_session,
                common_job_parameters,
            )
            cartography.intel.supabase.functions.sync(
                neo4j_session,
                api_session,
                common_job_parameters,
            )
            cartography.intel.supabase.storage.sync(
                neo4j_session,
                api_session,
                common_job_parameters,
            )
            cartography.intel.supabase.auth.sync(
                neo4j_session,
                api_session,
                common_job_parameters,
            )
            cartography.intel.supabase.network.sync(
                neo4j_session,
                api_session,
                common_job_parameters,
            )
            cartography.intel.supabase.branches.sync(
                neo4j_session,
                api_session,
                common_job_parameters,
            )
            cartography.intel.supabase.advisors.sync(
                neo4j_session,
                api_session,
                common_job_parameters,
            )

        # Remove projects deleted upstream only now that every surviving project's
        # children have been synced. The cascade takes their children with them:
        # child cleanups are scoped to PROJECT_REF and only run for projects that
        # still exist, so a deleted project's resources would otherwise be
        # unreachable orphans.
        common_job_parameters.pop("PROJECT_REF", None)
        cartography.intel.supabase.projects.cleanup(
            neo4j_session,
            common_job_parameters,
        )
