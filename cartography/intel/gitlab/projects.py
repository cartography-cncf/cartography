import logging
from typing import Any
from typing import Dict
from typing import List
from urllib.parse import unquote
from urllib.parse import urlparse

import gitlab
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gitlab.project import GitLabProjectSchema
from cartography.models.gitlab.repository import GitLabRepositorySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gitlab_projects(gitlab_url: str, gitlab_token: str) -> List[Dict[str, Any]]:
    """
    Fetches projects from the GitLab API.

    :param gitlab_url: URL of the GitLab instance
    :param gitlab_token: Personal access token for GitLab API authentication
    :return: A list of project details
    :raises ValueError: if gitlab_url or gitlab_token is not provided
    """
    if not gitlab_url or not gitlab_token:
        raise ValueError("GitLab URL and token are required")

    gl = gitlab.Gitlab(url=gitlab_url, private_token=gitlab_token)
    projects_iterator = gl.projects.list(iterator=True)

    projects = []
    for project in projects_iterator:
        projects.append(
            {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "url": project.web_url,
                "created_at": project.created_at,
                "last_activity_at": project.last_activity_at,
            },
        )

    logger.info(f"Found {len(projects)} GitLab projects")
    return projects


@timeit
def _extract_repo_name_from_url(url: str) -> str:
    """
    Extracts the repository name from the GitLab project URL.

    :param url: GitLab project web URL
    :return: Repository name extracted from URL path
    """
    parsed_url = urlparse(url)
    # Unquote in case of URL-encoded characters and strip leading slash
    return unquote(parsed_url.path).lstrip("/")


@timeit
def _transform_gitlab_projects(projects: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Transform GitLab project data for loading into Neo4j.

    :param projects: List of project data from GitLab API
    :return: Tuple of (projects_for_load, repositories_for_load)
    """
    projects_transformed = []
    repositories = []
    seen_repos = set()

    for project in projects:
        repo_name = _extract_repo_name_from_url(project["url"])
        repo_id = f"gitlab_{repo_name}"

        # Add repository_id for relationship
        project_data = {**project, "repository_id": repo_id}
        projects_transformed.append(project_data)

        # Collect unique repositories
        if repo_id not in seen_repos:
            repositories.append(
                {
                    "id": repo_id,
                    "name": repo_name,
                    "url": project["url"],
                },
            )
            seen_repos.add(repo_id)

    return projects_transformed, repositories


@timeit
def _load_gitlab_repositories(
    neo4j_session: neo4j.Session,
    repositories: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load GitLab repository nodes into Neo4j.

    :param neo4j_session: Neo4j session
    :param repositories: List of repository data
    :param update_tag: Update tag for tracking data freshness
    """
    logger.info(f"Loading {len(repositories)} GitLab repositories")
    load(
        neo4j_session,
        GitLabRepositorySchema(),
        repositories,
        lastupdated=update_tag,
    )


@timeit
def _load_gitlab_projects(
    neo4j_session: neo4j.Session,
    projects: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load GitLab project nodes and their relationships into Neo4j.

    :param neo4j_session: Neo4j session
    :param projects: List of transformed project data
    :param update_tag: Update tag for tracking data freshness
    """
    logger.info(f"Loading {len(projects)} GitLab projects")
    load(
        neo4j_session,
        GitLabProjectSchema(),
        projects,
        lastupdated=update_tag,
    )


@timeit
def _cleanup_gitlab_data(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Remove stale GitLab data from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters including UPDATE_TAG
    """
    # Cleanup projects
    GraphJob.from_node_schema(GitLabProjectSchema(), common_job_parameters).run(neo4j_session)
    # Cleanup repositories
    GraphJob.from_node_schema(GitLabRepositorySchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync_gitlab_projects(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    gitlab_token: str,
    update_tag: int,
) -> None:
    """
    Synchronizes GitLab projects data with Neo4j.

    :param neo4j_session: Neo4j session
    :param gitlab_url: The GitLab instance URL
    :param gitlab_token: GitLab API access token
    :param update_tag: Update tag for tracking data freshness
    """
    common_job_parameters = {
        "UPDATE_TAG": update_tag,
    }

    logger.info("Syncing GitLab projects")

    # Fetch data from GitLab API
    projects = get_gitlab_projects(gitlab_url, gitlab_token)

    # Transform data
    projects_data, repositories_data = _transform_gitlab_projects(projects)

    # Load repositories first (as they're referenced by projects)
    _load_gitlab_repositories(neo4j_session, repositories_data, update_tag)

    # Load projects and their relationships
    _load_gitlab_projects(neo4j_session, projects_data, update_tag)

    # Cleanup stale data
    _cleanup_gitlab_data(neo4j_session, common_job_parameters)
