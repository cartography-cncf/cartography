import logging

import neo4j

import cartography.intel.gitlab.branches
import cartography.intel.gitlab.dependencies
import cartography.intel.gitlab.dependency_files
import cartography.intel.gitlab.groups
import cartography.intel.gitlab.organizations
import cartography.intel.gitlab.projects
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_gitlab_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of GitLab data. Otherwise warn and exit.
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not all([config.gitlab_token, config.gitlab_organization_id]):
        logger.info(
            "GitLab import is not configured - skipping this module. "
            "See docs to configure (requires --gitlab-token-env-var and --gitlab-organization-id).",
        )
        return

    gitlab_url = config.gitlab_url
    token = config.gitlab_token
    organization_id = config.gitlab_organization_id

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "ORGANIZATION_ID": organization_id,
    }

    logger.info(
        f"Starting GitLab sync for organization {organization_id} at {gitlab_url}"
    )

    # Sync the specified organization (top-level group)
    organization = cartography.intel.gitlab.organizations.sync_gitlab_organizations(
        neo4j_session,
        gitlab_url,
        token,
        config.update_tag,
        common_job_parameters,
    )

    if not organization:
        logger.warning(f"Organization {organization_id} not found")
        return

    # Sync groups (nested subgroups within this organization)
    cartography.intel.gitlab.groups.sync_gitlab_groups(
        neo4j_session,
        gitlab_url,
        token,
        config.update_tag,
        common_job_parameters,
    )

    # Sync projects (within this organization and its groups)
    # Returns the projects list to avoid redundant API calls
    all_projects = cartography.intel.gitlab.projects.sync_gitlab_projects(
        neo4j_session,
        gitlab_url,
        token,
        config.update_tag,
        common_job_parameters,
    )

    org_url: str = organization["web_url"]

    # Sync branches  - pass projects to avoid re-fetching
    cartography.intel.gitlab.branches.sync_gitlab_branches(
        neo4j_session,
        gitlab_url,
        token,
        config.update_tag,
        common_job_parameters,
        all_projects,
    )

    # Sync dependency files
    cartography.intel.gitlab.dependency_files.sync_gitlab_dependency_files(
        neo4j_session,
        gitlab_url,
        token,
        config.update_tag,
        common_job_parameters,
        all_projects,
    )

    # Sync dependencies
    cartography.intel.gitlab.dependencies.sync_gitlab_dependencies(
        neo4j_session,
        gitlab_url,
        token,
        config.update_tag,
        common_job_parameters,
        all_projects,
    )

    # ========================================
    # Cleanup Phase - Run in reverse order (leaf to root)
    # ========================================
    logger.info("Starting GitLab cleanup phase")

    # Cleanup leaf nodes (dependencies, dependency_files, branches) for each project
    logger.info(f"Cleaning up leaf nodes for {len(all_projects)} projects")
    for project in all_projects:
        project_url: str = project["web_url"]

        # Cleanup dependencies
        cartography.intel.gitlab.dependencies.cleanup_dependencies(
            neo4j_session, common_job_parameters, project_url
        )

        # Cleanup dependency files
        cartography.intel.gitlab.dependency_files.cleanup_dependency_files(
            neo4j_session, common_job_parameters, project_url
        )

        # Cleanup branches
        cartography.intel.gitlab.branches.cleanup_branches(
            neo4j_session, common_job_parameters, project_url
        )

    # Cleanup projects with cascade delete
    logger.info("Cleaning up projects with cascade delete")
    cartography.intel.gitlab.projects.cleanup_projects(
        neo4j_session, common_job_parameters, org_url
    )

    # Cleanup groups with cascade delete
    logger.info("Cleaning up groups with cascade delete")
    cartography.intel.gitlab.groups.cleanup_groups(
        neo4j_session, common_job_parameters, org_url
    )

    # Cleanup organizations
    logger.info("Cleaning up organizations")
    cartography.intel.gitlab.organizations.cleanup_organizations(
        neo4j_session, common_job_parameters, gitlab_url
    )

    logger.info(f"GitLab ingestion completed for organization {organization_id}")
