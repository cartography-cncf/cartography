import logging
from typing import Any

import neo4j
import requests

import cartography.intel.gitlab.branches
import cartography.intel.gitlab.ci_config
import cartography.intel.gitlab.ci_variables
import cartography.intel.gitlab.container_image_attestations
import cartography.intel.gitlab.container_images
import cartography.intel.gitlab.container_repositories
import cartography.intel.gitlab.container_repository_tags
import cartography.intel.gitlab.dependencies
import cartography.intel.gitlab.dependency_files
import cartography.intel.gitlab.environments
import cartography.intel.gitlab.groups
import cartography.intel.gitlab.organizations
import cartography.intel.gitlab.projects
import cartography.intel.gitlab.runners
import cartography.intel.gitlab.supply_chain
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
        "org_id": organization_id,
    }

    logger.info(
        f"Starting GitLab sync for organization {organization_id} at {gitlab_url}"
    )

    # Sync the specified organization (top-level group)
    try:
        cartography.intel.gitlab.organizations.sync_gitlab_organizations(
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
        raise

    common_job_parameters["gitlab_url"] = gitlab_url

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

    # ========================================
    # CI/CD Phase
    # Runs before the container/dependency phase: CI/CD only depends on
    # `all_groups` and `all_projects`, so doing it early means the static
    # security signals (unpinned includes, unprotected runners, ...) land
    # in the graph even if the (slower / heavier) container scan fails.
    # ========================================

    # Sync CI/CD runners at instance, group, and project scopes.
    # Each scope returns a "skipped" set when a 403 was encountered — those
    # scopes must be excluded from the cleanup phase to avoid deleting
    # previously-ingested runners that we simply could not list this time.
    runners_skipped = cartography.intel.gitlab.runners.sync_gitlab_runners(
        neo4j_session,
        gitlab_url,
        token,
        config.update_tag,
        common_job_parameters,
        all_groups,
        all_projects,
    )

    # Sync CI/CD variables at group and project scopes.
    # Returns a {project_id: [variables]} map and a per-scope "skipped" set
    # (same data-loss-prevention rationale as runners above).
    variables_by_project, variables_skipped = (
        cartography.intel.gitlab.ci_variables.sync_gitlab_ci_variables(
            neo4j_session,
            gitlab_url,
            token,
            config.update_tag,
            common_job_parameters,
            all_groups,
            all_projects,
        )
    )

    # Sync environments and link them to CI/CD variables that apply to them
    # (exact match on environment_scope or wildcard "*"). Projects whose
    # variables could not be loaded this run are forwarded as `skip_projects`
    # so we don't refresh env nodes with empty `linked_variable_ids` and let
    # cleanup wipe HAS_CI_VARIABLE edges that should still be there.
    environments_skipped = (
        cartography.intel.gitlab.environments.sync_gitlab_environments(
            neo4j_session,
            gitlab_url,
            token,
            config.update_tag,
            common_job_parameters,
            all_projects,
            variables_by_project,
            skip_projects=variables_skipped["projects"],
        )
    )

    # Sync .gitlab-ci.yml configs (parsed pipeline summary + includes) and link
    # to project-level variables they reference. Same `skip_projects`
    # forwarding rationale as environments.
    ci_config_skipped = cartography.intel.gitlab.ci_config.sync_gitlab_ci_config(
        neo4j_session,
        gitlab_url,
        token,
        config.update_tag,
        common_job_parameters,
        all_projects,
        variables_by_project,
        skip_projects=variables_skipped["projects"],
    )

    # ========================================
    # Container Registry + Dependencies Phase
    # ========================================

    # Sync container repositories (includes cleanup since it's org-scoped)
    all_container_repositories = (
        cartography.intel.gitlab.container_repositories.sync_container_repositories(
            neo4j_session,
            gitlab_url,
            token,
            organization_id,
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
            organization_id,
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
        organization_id,
        all_container_repositories,
        config.update_tag,
        common_job_parameters,
    )

    # Sync container image attestations (includes cleanup since it's org-scoped)
    cartography.intel.gitlab.container_image_attestations.sync_container_image_attestations(
        neo4j_session,
        gitlab_url,
        token,
        organization_id,
        all_image_manifests,
        manifest_lists,
        config.update_tag,
        common_job_parameters,
    )

    # Sync supply chain (dockerfiles, provenance) and match to container images
    # Must happen after container images and tags are synced
    cartography.intel.gitlab.supply_chain.sync(
        neo4j_session,
        gitlab_url,
        token,
        organization_id,
        config.update_tag,
        common_job_parameters,
        all_projects,
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

    # Cleanup leaf nodes (dependencies, dependency_files, branches, project runners) for each project
    for project in all_projects:
        project_id: int = project["id"]

        # Cleanup dependencies
        cartography.intel.gitlab.dependencies.cleanup_dependencies(
            neo4j_session, common_job_parameters, project_id, gitlab_url
        )

        # Cleanup dependency files
        cartography.intel.gitlab.dependency_files.cleanup_dependency_files(
            neo4j_session, common_job_parameters, project_id, gitlab_url
        )

        # Cleanup branches
        cartography.intel.gitlab.branches.cleanup_branches(
            neo4j_session, common_job_parameters, project_id, gitlab_url
        )

        # Cleanup project-level runners — skip if the scope returned 403,
        # otherwise we'd delete every previously-ingested runner.
        if project_id not in runners_skipped["projects"]:
            cartography.intel.gitlab.runners.cleanup_project_runners(
                neo4j_session, common_job_parameters, project_id, gitlab_url
            )

        # Cleanup CI includes first, then the parent CIConfig — but skip if
        # the project's config was permission-denied this sync, otherwise
        # we'd delete a previously-ingested config on transient auth fail.
        if project_id not in ci_config_skipped:
            cartography.intel.gitlab.ci_config.cleanup_ci_includes(
                neo4j_session, common_job_parameters, project_id, gitlab_url
            )
            cartography.intel.gitlab.ci_config.cleanup_ci_configs(
                neo4j_session, common_job_parameters, project_id, gitlab_url
            )

        # Cleanup environments — skip if the scope returned 403.
        if project_id not in environments_skipped:
            cartography.intel.gitlab.environments.cleanup_environments(
                neo4j_session, common_job_parameters, project_id, gitlab_url
            )

        # Cleanup project-level CI/CD variables — skip if the scope returned 403.
        if project_id not in variables_skipped["projects"]:
            cartography.intel.gitlab.ci_variables.cleanup_project_variables(
                neo4j_session, common_job_parameters, project_id, gitlab_url
            )

    # Cleanup group-level runners and CI/CD variables (one cleanup per group),
    # skipping any scope that returned 403 during the sync.
    for group in all_groups:
        group_id_int = group["id"]
        if group_id_int not in runners_skipped["groups"]:
            cartography.intel.gitlab.runners.cleanup_group_runners(
                neo4j_session, common_job_parameters, group_id_int, gitlab_url
            )
        if group_id_int not in variables_skipped["groups"]:
            cartography.intel.gitlab.ci_variables.cleanup_group_variables(
                neo4j_session, common_job_parameters, group_id_int, gitlab_url
            )

    # Cleanup instance-level runners (scoped to the organization).
    # Skip if the /runners/all endpoint returned 403 (admin scope missing).
    if not runners_skipped["instance"]:
        cartography.intel.gitlab.runners.cleanup_instance_runners(
            neo4j_session, common_job_parameters, organization_id, gitlab_url
        )

    # Cleanup projects with cascade delete
    cartography.intel.gitlab.projects.cleanup_projects(
        neo4j_session, common_job_parameters, organization_id, gitlab_url
    )

    # Cleanup users
    cartography.intel.gitlab.users.cleanup_users(
        neo4j_session, common_job_parameters, organization_id, gitlab_url
    )

    # Cleanup groups with cascade delete
    cartography.intel.gitlab.groups.cleanup_groups(
        neo4j_session, common_job_parameters, organization_id, gitlab_url
    )

    # Cleanup organizations
    cartography.intel.gitlab.organizations.cleanup_organizations(
        neo4j_session, common_job_parameters, gitlab_url
    )

    logger.info(f"GitLab ingestion completed for organization {organization_id}")
