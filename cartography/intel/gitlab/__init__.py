import logging
from typing import Any

import neo4j
import requests

import cartography.intel.gitlab.branches
import cartography.intel.gitlab.container_image_attestations
import cartography.intel.gitlab.container_images
import cartography.intel.gitlab.container_repositories
import cartography.intel.gitlab.container_repository_tags
import cartography.intel.gitlab.dependencies
import cartography.intel.gitlab.dependency_files
import cartography.intel.gitlab.groups
import cartography.intel.gitlab.organizations
import cartography.intel.gitlab.projects
import cartography.intel.gitlab.users
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

    gitlab_url: str = config.gitlab_url
    token: str = config.gitlab_token
    organization_id: int = config.gitlab_organization_id

    common_job_parameters: dict[str, Any] = {
        "UPDATE_TAG": config.update_tag,
        "ORGANIZATION_ID": organization_id,
    }

    logger.info(
        f"Starting GitLab sync for organization {organization_id} at {gitlab_url}"
    )

    # Sync the specified organization (top-level group)
    try:
        organization = cartography.intel.gitlab.organizations.sync_gitlab_organizations(
            neo4j_session,
            gitlab_url,
            token,
            config.update_tag,
            common_job_parameters,
        )
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            logger.error(
                f"Organization {organization_id} not found at {gitlab_url}. "
                "Please verify the organization ID is correct and the token has access."
            )
        elif e.response is not None and e.response.status_code == 401:
            logger.error(
                f"Authentication failed for GitLab at {gitlab_url}. "
                "Please verify the token is valid and has required scopes (read_api)."
            )
        else:
            logger.error(
                f"Failed to fetch organization {organization_id} from {gitlab_url}: {e}"
            )
        return

    org_url: str = organization["web_url"]

    # Add org_url to common_job_parameters for cleanup jobs
    common_job_parameters["org_url"] = org_url

    # Sync groups (nested subgroups within this organization)
    # Returns the groups list to avoid redundant API calls
    all_groups = cartography.intel.gitlab.groups.sync_gitlab_groups(
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

    # Sync users (members of organization and groups) with commit activity
    # Must happen after projects sync since we need projects to fetch commits
    cartography.intel.gitlab.users.sync_gitlab_users(
        neo4j_session,
        gitlab_url,
        token,
        config.update_tag,
        common_job_parameters,
        all_groups,
        all_projects,
        config.gitlab_commits_since_days,
    )

    # Sync container repositories (includes cleanup since it's org-scoped)
    all_container_repositories = (
        cartography.intel.gitlab.container_repositories.sync_container_repositories(
            neo4j_session,
            gitlab_url,
            token,
            org_url,
            organization_id,
            config.update_tag,
            common_job_parameters,
        )
    )

    # Sync container images before tags since tags have REFERENCES relationship to images
    # Returns raw manifests and manifest lists for downstream attestation sync
    all_image_manifests, manifest_lists = (
        cartography.intel.gitlab.container_images.sync_container_images(
            neo4j_session,
            gitlab_url,
            token,
            org_url,
            all_container_repositories,
            config.update_tag,
            common_job_parameters,
        )
    )

    # Sync container repository tags (includes cleanup since it's org-scoped)
    cartography.intel.gitlab.container_repository_tags.sync_container_repository_tags(
        neo4j_session,
        gitlab_url,
        token,
        org_url,
        all_container_repositories,
        config.update_tag,
        common_job_parameters,
    )

    # Sync container image attestations (includes cleanup since it's org-scoped)
    cartography.intel.gitlab.container_image_attestations.sync_container_image_attestations(
        neo4j_session,
        gitlab_url,
        token,
        org_url,
        all_image_manifests,
        manifest_lists,
        config.update_tag,
        common_job_parameters,
    )

    # Sync branches - pass projects to avoid re-fetching
    cartography.intel.gitlab.branches.sync_gitlab_branches(
        neo4j_session,
        gitlab_url,
        token,
        config.update_tag,
        common_job_parameters,
        all_projects,
    )

    # Sync dependency files - returns data to avoid duplicate API calls in dependencies sync
    dependency_files_by_project = (
        cartography.intel.gitlab.dependency_files.sync_gitlab_dependency_files(
            neo4j_session,
            gitlab_url,
            token,
            config.update_tag,
            common_job_parameters,
            all_projects,
        )
    )

    # Sync dependencies - pass pre-fetched dependency files to avoid duplicate API calls
    cartography.intel.gitlab.dependencies.sync_gitlab_dependencies(
        neo4j_session,
        gitlab_url,
        token,
        config.update_tag,
        common_job_parameters,
        all_projects,
        dependency_files_by_project,
    )

    # ========================================
    # Cleanup Phase - Run in reverse order (leaf to root)
    # ========================================
    logger.info("Starting GitLab cleanup phase")

    # Cleanup leaf nodes (dependencies, dependency_files, branches) for each project
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
    cartography.intel.gitlab.projects.cleanup_projects(
        neo4j_session, common_job_parameters, org_url
    )

    # Cleanup users
    cartography.intel.gitlab.users.cleanup_users(
        neo4j_session, common_job_parameters, org_url
    )

    # Cleanup groups with cascade delete
    cartography.intel.gitlab.groups.cleanup_groups(
        neo4j_session, common_job_parameters, org_url
    )

    # Cleanup organizations
    cartography.intel.gitlab.organizations.cleanup_organizations(
        neo4j_session, common_job_parameters, gitlab_url
    )

    logger.info(f"GitLab ingestion completed for organization {organization_id}")
