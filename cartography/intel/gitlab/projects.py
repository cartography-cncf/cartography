"""
GitLab Projects Intelligence Module
"""

import asyncio
import json
import logging
from typing import Any

import httpx
import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gitlab.organizations import get_organization
from cartography.intel.gitlab.organizations import get_organizations
from cartography.models.gitlab.projects import GitLabProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Concurrency settings for language fetching
_MAX_CONCURRENT_REQUESTS = 10
_REQUEST_TIMEOUT = 60.0


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
                f"HTTP error fetching languages for project {project_id}: {e.response.status_code}"
            )
            return (project_id, {})
        except Exception as e:
            logger.debug(f"Error fetching languages for project {project_id}: {e}")
            return (project_id, {})


async def _fetch_all_languages(
    gitlab_url: str,
    token: str,
    projects: list[dict[str, Any]],
) -> dict[int, dict[str, float]]:
    """
    Fetch languages for all projects concurrently using asyncio.

    :param gitlab_url: The GitLab instance URL.
    :param token: The GitLab API token.
    :param projects: List of raw project dicts (must have 'id' key).
    :return: Dict mapping project_id to language dict {name: percentage}.
    """
    if not projects:
        return {}

    headers = {"PRIVATE-TOKEN": token}
    semaphore = asyncio.Semaphore(_MAX_CONCURRENT_REQUESTS)

    async with httpx.AsyncClient(headers=headers, timeout=_REQUEST_TIMEOUT) as client:
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
            logger.debug(f"Exception fetching languages: {result}")

    return languages_by_project


def fetch_all_projects(gitlab_url: str, token: str) -> list[dict[str, Any]]:
    """
    Fetch all projects across all organizations from GitLab.

    This is a helper function to avoid redundant API calls when multiple
    sync functions need the same project list.
    """
    logger.info("Fetching all projects across all organizations")
    organizations = get_organizations(gitlab_url, token)

    all_projects = []
    for org in organizations:
        org_id: int = org["id"]
        org_name: str = org["name"]
        logger.info(f"Fetching projects for organization: {org_name}")
        org_projects = get_projects(gitlab_url, token, org_id)
        if org_projects:
            all_projects.extend(org_projects)

    logger.info(
        f"Fetched total of {len(all_projects)} projects across all organizations"
    )
    return all_projects


def get_projects(gitlab_url: str, token: str, group_id: int) -> list[dict[str, Any]]:
    """
    Fetch all projects for a specific group from GitLab using REST API.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Use the /groups/:id/projects endpoint to get all projects in this group
    api_url = f"{gitlab_url}/api/v4/groups/{group_id}/projects"
    params = {
        "per_page": 100,  # Max items per page
        "page": 1,
        "include_subgroups": True,  # Include projects from subgroups
    }

    projects = []

    logger.info(f"Fetching projects for group ID {group_id} from {gitlab_url}")

    while True:
        response = requests.get(api_url, headers=headers, params=params, timeout=60)
        response.raise_for_status()

        page_projects = response.json()

        if not page_projects:
            # No more data
            break

        projects.extend(page_projects)

        logger.info(f"Fetched {len(page_projects)} projects from page {params['page']}")

        # Check if there's a next page
        next_page = response.headers.get("x-next-page")
        if not next_page:
            # No more pages
            break

        params["page"] = int(next_page)

    logger.info(f"Fetched total of {len(projects)} projects for group ID {group_id}")
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

    logger.info(f"Transformed {len(transformed)} projects (group projects only)")
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
    logger.info(f"Loading {len(projects)} projects for organization {org_url}")
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
    logger.info(f"Running GitLab projects cleanup for organization {org_url}")
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

    logger.info(f"Syncing GitLab projects for organization {organization_id}")

    # Fetch the organization to get its URL
    org = get_organization(gitlab_url, token, organization_id)
    org_url: str = org["web_url"]
    org_name: str = org["name"]

    logger.info(f"Syncing projects for organization: {org_name}")

    # Fetch ALL projects for this organization at once (includes all nested groups)
    raw_projects = get_projects(gitlab_url, token, organization_id)

    if not raw_projects:
        logger.info(f"No projects found for organization {org_name}")
        return []

    # Fetch languages for all projects concurrently
    logger.info(f"Fetching languages for {len(raw_projects)} projects")
    languages_by_project = asyncio.run(
        _fetch_all_languages(gitlab_url, token, raw_projects)
    )
    projects_with_languages = sum(1 for langs in languages_by_project.values() if langs)
    logger.info(f"Found languages for {projects_with_languages} projects")

    transformed_projects = transform_projects(
        raw_projects, org_url, languages_by_project
    )

    if not transformed_projects:
        logger.info(f"No group projects found for organization {org_name}")
        return raw_projects

    logger.info(
        f"Found {len(transformed_projects)} projects in organization {org_name}"
    )

    load_projects(neo4j_session, transformed_projects, org_url, update_tag)

    logger.info("GitLab projects sync completed")
    return raw_projects
