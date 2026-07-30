import logging

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

    # GET /v1/projects only returns projects this token's user created, so it cannot
    # decide which projects an organization has. It is fetched once purely to enrich
    # the organization-scoped listings with the `database` object they omit.
    enrichment_by_ref = {
        project["ref"]: project
        for project in cartography.intel.supabase.projects.get(
            api_session,
            config.supabase_base_url,
        )
    }

    for organization in organizations:
        org_slug = organization["slug"]
        common_job_parameters["ORG_SLUG"] = org_slug
        cartography.intel.supabase.organizations.sync_members(
            neo4j_session,
            api_session,
            common_job_parameters,
        )

        # The organization-scoped listing is the authority for what exists, so that
        # the cascading project cleanup below can never delete a project that the
        # organization still lists.
        projects = [
            cartography.intel.supabase.projects.merge_project(
                org_project,
                org_slug,
                enrichment_by_ref.get(org_project["ref"]),
            )
            for org_project in cartography.intel.supabase.projects.get_org_projects(
                api_session,
                config.supabase_base_url,
                org_slug,
            )
        ]
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
