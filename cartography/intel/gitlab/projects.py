"""
GitLab Projects Intelligence Module
"""

import asyncio
import json
import logging
from typing import Any

import httpx
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gitlab.organizations import get_organization
from cartography.intel.gitlab.util import get_paginated
from cartography.models.gitlab.projects import GitLabProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Default concurrency settings for language fetching (can be overridden via config)
DEFAULT_MAX_CONCURRENT_REQUESTS = 10
DEFAULT_REQUEST_TIMEOUT = 60.0


async def _fetch_project_languages(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    gitlab_url: str,
    project_id: int,
) -> tuple[int, dict[str, float]]:
    """
    Fetch languages for a single project.

    :param client: The httpx async client.
    :param semaphore: Semaphore to limit concurrent requests.
    :param gitlab_url: The GitLab instance URL.
    :param project_id: The numeric project ID.
    :return: A tuple of (project_id, language_dict) where language_dict maps name to percentage.
    """
    async with semaphore:
        try:
            url = f"{gitlab_url}/api/v4/projects/{project_id}/languages"
            response = await client.get(url)
            response.raise_for_status()
            # GitLab returns {language_name: percentage, ...}
            return (project_id, response.json())
        except httpx.HTTPStatusError as e:
            logger.debug(
                "HTTP error fetching languages for project %s: %s",
                project_id, e.response.status_code,
            )
            return (project_id, {})
        except Exception as e:
            logger.debug("Error fetching languages for project %s: %s", project_id, e)
            return (project_id, {})


async def _fetch_all_languages(
    gitlab_url: str,
    token: str,
    projects: list[dict[str, Any]],
    max_concurrent_requests: int = DEFAULT_MAX_CONCURRENT_REQUESTS,
) -> dict[int, dict[str, float]]:
    """
    Fetch languages for all projects concurrently using asyncio.

    :param gitlab_url: The GitLab instance URL.
    :param token: The GitLab API token.
    :param projects: List of raw project dicts (must have 'id' key).
    :param max_concurrent_requests: Maximum concurrent API requests (default: 10).
    :return: Dict mapping project_id to language dict {name: percentage}.
    """
    if not projects:
        return {}

    headers = {"Authorization": f"Bearer {token}"}
    semaphore = asyncio.Semaphore(max_concurrent_requests)

    async with httpx.AsyncClient(
        headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT
    ) as client:
        tasks = [
            _fetch_project_languages(client, semaphore, gitlab_url, project["id"])
            for project in projects
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    # Build dict from results, filtering out exceptions
    languages_by_project: dict[int, dict[str, float]] = {}
    for result in results:
        if isinstance(result, tuple):
            project_id, languages = result
            languages_by_project[project_id] = languages
        elif isinstance(result, Exception):
            logger.debug("Exception fetching languages: %s", result)

    return languages_by_project


def get_projects(gitlab_url: str, token: str, group_id: int) -> list[dict[str, Any]]:
    """
    Fetch all projects for a specific group from GitLab.
    """
    logger.debug("Fetching projects for group ID %s", group_id)
    projects = get_paginated(
        gitlab_url,
        token,
        f"/api/v4/groups/{group_id}/projects",
        extra_params={"include_subgroups": True},
    )
    logger.debug("Fetched %s projects for group ID %s", len(projects), group_id)
    return projects


def transform_projects(
    raw_projects: list[dict[str, Any]],
    org_url: str,
    languages_by_project: dict[int, dict[str, float]] | None = None,
) -> list[dict[str, Any]]:
    """
    Transform raw GitLab project data into the format expected by the schema.

    :param raw_projects: List of raw project dicts from GitLab API.
    :param org_url: The organization URL.
    :param languages_by_project: Optional dict mapping project_id to language dict.
    :return: List of transformed project dicts.
    """
    if languages_by_project is None:
        languages_by_project = {}

    transformed = []

    for project in raw_projects:
        # Extract group information from namespace
        namespace = project.get("namespace", {})
        if (
            namespace.get("kind") != "group"
        ):  # Only process projects that belong to groups
            continue

        namespace_url = namespace.get("web_url")

        # Determine if this project is in the org directly or in a nested group
        if namespace_url == org_url:
            # Org-level project - no group relationship
            group_url = None
        else:
            # Group-level project - has relationship to nested group
            group_url = namespace_url

        # Get languages for this project (stored as JSON string for Neo4j)
        project_id: int = project.get("id", 0)
        project_languages = languages_by_project.get(project_id, {})
        # Convert to JSON string for storage in Neo4j
        languages_json = json.dumps(project_languages) if project_languages else None

        transformed_project = {
            "web_url": project.get("web_url"),
            "name": project.get("name"),
            "path": project.get("path"),
            "path_with_namespace": project.get("path_with_namespace"),
            "description": project.get("description"),
            "visibility": project.get("visibility"),
            "default_branch": project.get("default_branch"),
            "archived": project.get("archived", False),
            "created_at": project.get("created_at"),
            "last_activity_at": project.get("last_activity_at"),
            "org_url": org_url,
            "group_url": group_url,
            "languages": languages_json,
        }
        transformed.append(transformed_project)

    logger.debug("Transformed %s projects (group projects only)", len(transformed))
    return transformed


@timeit
def load_projects(
    neo4j_session: neo4j.Session,
    projects: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    """
    Load GitLab projects into the graph for a specific organization.
    """
    logger.debug("Loading %s projects for organization %s", len(projects), org_url)
    load(
        neo4j_session,
        GitLabProjectSchema(),
        projects,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def cleanup_projects(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    org_url: str,
) -> None:
    """
    Remove stale GitLab projects from the graph for a specific organization.
    Uses cascade delete to also remove child branches, dependency files, and dependencies.
    """
    logger.debug("Running GitLab projects cleanup for organization %s", org_url)
    cleanup_params = {**common_job_parameters, "org_url": org_url}
    GraphJob.from_node_schema(
        GitLabProjectSchema(), cleanup_params, cascade_delete=True
    ).run(neo4j_session)


@timeit
def sync_gitlab_projects(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    token: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Sync GitLab projects for a specific organization.

    The organization ID should be passed in common_job_parameters["ORGANIZATION_ID"].
    This also fetches and stores language information for each project.

    Returns the raw projects list to avoid redundant API calls in downstream sync functions.
    """
    organization_id = common_job_parameters.get("ORGANIZATION_ID")
    if not organization_id:
        raise ValueError("ORGANIZATION_ID must be provided in common_job_parameters")

    logger.info("Syncing GitLab projects for organization %s", organization_id)

    # Fetch the organization to get its URL
    org = get_organization(gitlab_url, token, organization_id)
    org_url: str = org["web_url"]
    org_name: str = org["name"]

    logger.info("Syncing projects for organization: %s", org_name)

    # Fetch ALL projects for this organization at once (includes all nested groups)
    raw_projects = get_projects(gitlab_url, token, organization_id)

    if not raw_projects:
        logger.debug("No projects found for organization %s", org_name)
        return []

    # Fetch languages for all projects concurrently
    logger.debug("Fetching languages for %s projects", len(raw_projects))
    languages_by_project = asyncio.run(
        _fetch_all_languages(gitlab_url, token, raw_projects)
    )
    projects_with_languages = sum(1 for langs in languages_by_project.values() if langs)
    logger.debug("Found languages for %s projects", projects_with_languages)

    transformed_projects = transform_projects(
        raw_projects, org_url, languages_by_project
    )

    if not transformed_projects:
        logger.debug("No group projects found for organization %s", org_name)
        return raw_projects

    logger.debug(
        "Found %d projects in organization %s", len(transformed_projects), org_name
    )

    load_projects(neo4j_session, transformed_projects, org_url, update_tag)

    logger.info("GitLab projects sync completed")
    return raw_projects
