import asyncio
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
import cartography.intel.gitlab.terraform_states
import cartography.intel.gitlab.users
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)

VALID_SYNC_RESOURCES = frozenset(
    [
        "organizations",
        "groups",
        "projects",
        "users",
        "runners",
        "ci_variables",
        "environments",
        "ci_config",
        "container_repositories",
        "branches",
        "dependencies",
        "terraform_states",
    ]
)


def parse_and_validate_gitlab_requested_syncs(requested_syncs_str: str) -> list[str]:
    validated: list[str] = []
    for resource in requested_syncs_str.split(","):
        resource = resource.strip()
        if resource in VALID_SYNC_RESOURCES:
            validated.append(resource)
        else:
            valid = ", ".join(sorted(VALID_SYNC_RESOURCES))
            raise ValueError(
                f'Error parsing `--gitlab-requested-syncs`. Unknown resource "{resource}". '
                f"Valid values: {valid}."
            )
    return validated


def parse_group_paths(group_paths_str: str) -> set[str]:
    return {p.strip() for p in group_paths_str.split(",") if p.strip()}


def _path_matches(full_path: str, allowed_paths: set[str]) -> bool:
    segments = full_path.split("/")
    for allowed in allowed_paths:
        allowed_segments = allowed.split("/")
        n = len(allowed_segments)
        for i in range(len(segments) - n + 1):
            if segments[i : i + n] == allowed_segments:
                return True
    return False


def _filter_groups_by_paths(
    groups: list[dict[str, Any]], allowed_paths: set[str]
) -> list[dict[str, Any]]:
    return [g for g in groups if _path_matches(g.get("full_path", ""), allowed_paths)]


def _filter_projects_by_paths(
    projects: list[dict[str, Any]], allowed_paths: set[str]
) -> list[dict[str, Any]]:
    return [
        p
        for p in projects
        if _path_matches(p.get("path_with_namespace", ""), allowed_paths)
    ]


@timeit
def start_gitlab_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not all([config.gitlab_token, config.gitlab_organization_id]):
        logger.info(
            "GitLab import is not configured - skipping this module. "
            "See docs to configure (requires --gitlab-token-env-var and --gitlab-organization-id).",
        )
        return

    gitlab_url: str = config.gitlab_url
    token: str = config.gitlab_token
    organization_id: int = config.gitlab_organization_id

    requested_syncs: set[str] = set(VALID_SYNC_RESOURCES)
    if config.gitlab_requested_syncs:
        requested_syncs = set(
            parse_and_validate_gitlab_requested_syncs(config.gitlab_requested_syncs)
        )
        logger.info("GitLab sync scoped to resource types: %s", sorted(requested_syncs))

    allowed_group_paths: set[str] | None = None
    if config.gitlab_group_paths:
        allowed_group_paths = parse_group_paths(config.gitlab_group_paths)
        logger.info(
            "GitLab sync scoped to group paths: %s", sorted(allowed_group_paths)
        )

    common_job_parameters: dict[str, Any] = {
        "UPDATE_TAG": config.update_tag,
        "ORGANIZATION_ID": organization_id,
        "org_id": organization_id,
    }

    logger.info(
        "Starting GitLab sync for organization %s at %s", organization_id, gitlab_url
    )

    if "organizations" in requested_syncs:
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
                    "Organization %s not found at %s. "
                    "Please verify the organization ID is correct and the token has access.",
                    organization_id,
                    gitlab_url,
                )
            elif e.response is not None and e.response.status_code == 401:
                logger.error(
                    "Authentication failed for GitLab at %s. "
                    "Please verify the token is valid and has required scopes (read_api).",
                    gitlab_url,
                )
            else:
                logger.error(
                    "Failed to fetch organization %s from %s: %s",
                    organization_id,
                    gitlab_url,
                    e,
                )
            raise

    common_job_parameters["gitlab_url"] = gitlab_url

    all_groups: list[dict[str, Any]] = []
    if "groups" in requested_syncs:
        if allowed_group_paths is not None:
            raw_groups = cartography.intel.gitlab.groups.get_groups(
                gitlab_url, token, organization_id
            )
            transformed_groups = cartography.intel.gitlab.groups.transform_groups(
                raw_groups, organization_id, gitlab_url
            )
            before = len(transformed_groups)
            filtered_groups = _filter_groups_by_paths(
                transformed_groups, allowed_group_paths
            )
            logger.info(
                "Group path filter: %d → %d groups", before, len(filtered_groups)
            )
            cartography.intel.gitlab.groups.load_groups(
                neo4j_session,
                filtered_groups,
                organization_id,
                gitlab_url,
                config.update_tag,
            )
            all_groups = [
                g
                for g in raw_groups
                if any(t["id"] == g.get("id") for t in filtered_groups)
            ]
        else:
            all_groups = cartography.intel.gitlab.groups.sync_gitlab_groups(
                neo4j_session,
                gitlab_url,
                token,
                config.update_tag,
                common_job_parameters,
            )

    all_projects: list[dict[str, Any]] = []
    _skip_cleanup = False
    if "projects" in requested_syncs:
        if allowed_group_paths is not None:
            raw_projects = cartography.intel.gitlab.projects.get_projects(
                gitlab_url, token, organization_id
            )
            if raw_projects:
                before = len(raw_projects)
                filtered_raw_projects = _filter_projects_by_paths(
                    raw_projects, allowed_group_paths
                )
                logger.info(
                    "Group path filter: %d → %d projects",
                    before,
                    len(filtered_raw_projects),
                )
                if not filtered_raw_projects:
                    logger.warning(
                        "Group path filter matched 0 of %d projects — "
                        "paths %s may be mistyped. Skipping cleanup to prevent data loss.",
                        before,
                        sorted(allowed_group_paths),
                    )
                    _skip_cleanup = True
                if not _skip_cleanup:
                    org = cartography.intel.gitlab.organizations.get_organization(
                        gitlab_url, token, organization_id
                    )
                    languages_by_project = asyncio.run(
                        cartography.intel.gitlab.projects._fetch_all_languages(
                            gitlab_url, token, filtered_raw_projects
                        )
                    )
                    filtered_projects = (
                        cartography.intel.gitlab.projects.transform_projects(
                            filtered_raw_projects,
                            organization_id,
                            org["web_url"],
                            gitlab_url,
                            languages_by_project,
                        )
                    )
                    cartography.intel.gitlab.projects.load_projects(
                        neo4j_session,
                        filtered_projects,
                        organization_id,
                        gitlab_url,
                        config.update_tag,
                    )
                    all_projects = filtered_raw_projects
        else:
            all_projects = cartography.intel.gitlab.projects.sync_gitlab_projects(
                neo4j_session,
                gitlab_url,
                token,
                config.update_tag,
                common_job_parameters,
            )

    if "users" in requested_syncs:
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

    runners_skipped: dict[str, Any] = {
        "projects": set(),
        "groups": set(),
        "instance": False,
    }
    if "runners" in requested_syncs:
        runners_skipped = cartography.intel.gitlab.runners.sync_gitlab_runners(
            neo4j_session,
            gitlab_url,
            token,
            config.update_tag,
            common_job_parameters,
            all_groups,
            all_projects,
        )

    variables_by_project: dict[int, list[dict[str, Any]]] = {}
    variables_skipped: dict[str, Any] = {"projects": set(), "groups": set()}
    if "ci_variables" in requested_syncs:
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

    environments_skipped: set[int] = set()
    if "environments" in requested_syncs:
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

    ci_config_skipped: set[int] = set()
    if "ci_config" in requested_syncs:
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

    all_container_repositories: list[dict[str, Any]] = []
    if "container_repositories" in requested_syncs:
        if allowed_group_paths is not None:
            allowed_project_ids = [p["id"] for p in all_projects]
            raw_repos = cartography.intel.gitlab.container_repositories.get_container_repositories_for_projects(
                gitlab_url, token, allowed_project_ids
            )
            logger.info(
                "Container repository per-project fetch: got %d repos for %d projects",
                len(raw_repos),
                len(allowed_project_ids),
            )
            transformed_repos = cartography.intel.gitlab.container_repositories.transform_container_repositories(
                raw_repos
            )
            cartography.intel.gitlab.container_repositories.load_container_repositories(
                neo4j_session,
                transformed_repos,
                organization_id,
                gitlab_url,
                config.update_tag,
            )
            cartography.intel.gitlab.container_repositories.cleanup_container_repositories(
                neo4j_session, common_job_parameters
            )
            all_container_repositories = raw_repos
        else:
            all_container_repositories = cartography.intel.gitlab.container_repositories.sync_container_repositories(
                neo4j_session,
                gitlab_url,
                token,
                organization_id,
                organization_id,
                config.update_tag,
                common_job_parameters,
            )

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

        cartography.intel.gitlab.container_repository_tags.sync_container_repository_tags(
            neo4j_session,
            gitlab_url,
            token,
            organization_id,
            all_container_repositories,
            config.update_tag,
            common_job_parameters,
        )

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

        cartography.intel.gitlab.supply_chain.sync(
            neo4j_session,
            gitlab_url,
            token,
            organization_id,
            config.update_tag,
            common_job_parameters,
            all_projects,
        )

    if "branches" in requested_syncs:
        cartography.intel.gitlab.branches.sync_gitlab_branches(
            neo4j_session,
            gitlab_url,
            token,
            config.update_tag,
            common_job_parameters,
            all_projects,
        )

    dependency_files_by_project: dict[str, list[dict[str, Any]]] = {}
    if "dependencies" in requested_syncs:
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

        cartography.intel.gitlab.dependencies.sync_gitlab_dependencies(
            neo4j_session,
            gitlab_url,
            token,
            config.update_tag,
            common_job_parameters,
            all_projects,
            dependency_files_by_project,
        )

    terraform_synced_project_ids: set[int] = set()
    if "terraform_states" in requested_syncs:
        synced_ids = (
            cartography.intel.gitlab.terraform_states.sync_gitlab_terraform_states(
                neo4j_session,
                gitlab_url,
                token,
                config.update_tag,
                common_job_parameters,
                all_projects,
            )
        )
        terraform_synced_project_ids = set(synced_ids)

    # ========================================
    # Cleanup Phase - Run in reverse order (leaf to root)
    # ========================================
    if _skip_cleanup:
        logger.warning("Skipping cleanup phase: group path filter matched no projects.")
        return

    logger.info("Starting GitLab cleanup phase")

    for project in all_projects:
        project_id: int = project["id"]

        if "dependencies" in requested_syncs:
            cartography.intel.gitlab.dependencies.cleanup_dependencies(
                neo4j_session, common_job_parameters, project_id, gitlab_url
            )
            cartography.intel.gitlab.dependency_files.cleanup_dependency_files(
                neo4j_session, common_job_parameters, project_id, gitlab_url
            )

        if "branches" in requested_syncs:
            cartography.intel.gitlab.branches.cleanup_branches(
                neo4j_session, common_job_parameters, project_id, gitlab_url
            )

        if (
            "runners" in requested_syncs
            and project_id not in runners_skipped["projects"]
        ):
            cartography.intel.gitlab.runners.cleanup_project_runners(
                neo4j_session, common_job_parameters, project_id, gitlab_url
            )

        if "ci_config" in requested_syncs and project_id not in ci_config_skipped:
            cartography.intel.gitlab.ci_config.cleanup_ci_includes(
                neo4j_session, common_job_parameters, project_id, gitlab_url
            )
            cartography.intel.gitlab.ci_config.cleanup_ci_configs(
                neo4j_session, common_job_parameters, project_id, gitlab_url
            )

        if "environments" in requested_syncs and project_id not in environments_skipped:
            cartography.intel.gitlab.environments.cleanup_environments(
                neo4j_session, common_job_parameters, project_id, gitlab_url
            )

        if (
            "ci_variables" in requested_syncs
            and project_id not in variables_skipped["projects"]
        ):
            cartography.intel.gitlab.ci_variables.cleanup_project_variables(
                neo4j_session, common_job_parameters, project_id, gitlab_url
            )

        if (
            "terraform_states" in requested_syncs
            and project_id in terraform_synced_project_ids
        ):
            cartography.intel.gitlab.terraform_states.cleanup_terraform_states(
                neo4j_session, common_job_parameters, project_id, gitlab_url
            )

    if "runners" in requested_syncs:
        for group in all_groups:
            group_id_int = group["id"]
            if group_id_int not in runners_skipped["groups"]:
                cartography.intel.gitlab.runners.cleanup_group_runners(
                    neo4j_session, common_job_parameters, group_id_int, gitlab_url
                )

        if not runners_skipped["instance"]:
            cartography.intel.gitlab.runners.cleanup_instance_runners(
                neo4j_session, common_job_parameters, organization_id, gitlab_url
            )

    if "ci_variables" in requested_syncs:
        for group in all_groups:
            group_id_int = group["id"]
            if group_id_int not in variables_skipped["groups"]:
                cartography.intel.gitlab.ci_variables.cleanup_group_variables(
                    neo4j_session, common_job_parameters, group_id_int, gitlab_url
                )

    if "projects" in requested_syncs:
        cartography.intel.gitlab.projects.cleanup_projects(
            neo4j_session, common_job_parameters, organization_id, gitlab_url
        )

    if "users" in requested_syncs:
        cartography.intel.gitlab.users.cleanup_users(
            neo4j_session, common_job_parameters, organization_id, gitlab_url
        )

    if "groups" in requested_syncs:
        cartography.intel.gitlab.groups.cleanup_groups(
            neo4j_session, common_job_parameters, organization_id, gitlab_url
        )

    if "organizations" in requested_syncs:
        cartography.intel.gitlab.organizations.cleanup_organizations(
            neo4j_session, common_job_parameters, gitlab_url
        )

    logger.info("GitLab ingestion completed for organization %s", organization_id)
