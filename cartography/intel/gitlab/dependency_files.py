"""
GitLab Dependency Files Intelligence Module
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gitlab.util import check_rate_limit_remaining
from cartography.intel.gitlab.util import make_request_with_retry
from cartography.models.gitlab.manifests import GitLabDependencyFileSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_dependency_files(
    gitlab_url: str, token: str, project_id: int
) -> list[dict[str, Any]]:
    """
    Search repository tree for dependency manifest files.

    This recursively searches the entire repository tree for known dependency manifest files
    (package.json, requirements.txt, go.mod, etc.) using the Repository Tree API.

    Uses retry logic with exponential backoff for rate limiting and transient errors.
    """
    # Known dependency manifest files to search for
    manifest_files = {
        "package.json",
        "package-lock.json",
        "requirements.txt",
        "Pipfile",
        "Pipfile.lock",
        "go.mod",
        "go.sum",
        "Gemfile",
        "Gemfile.lock",
        "pom.xml",
        "build.gradle",
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    logger.debug(
        f"Searching for dependency files in project ID {project_id} from {gitlab_url}"
    )

    # breadth first search to get manifest files in the repo tree
    paths_to_search: list[str] = [""]
    found_files: list[dict[str, Any]] = []

    while paths_to_search:
        current_path = paths_to_search.pop(0)

        api_url = f"{gitlab_url}/api/v4/projects/{project_id}/repository/tree"
        params: dict[str, Any] = {
            "per_page": 100,
            "page": 1,
            "recursive": False,
        }

        if current_path:
            params["path"] = current_path

        # Paginate through tree items at this path
        while True:
            response = make_request_with_retry("GET", api_url, headers, params)

            if response.status_code == 404:
                # Path doesn't exist or repository is empty
                logger.debug(f"Path not found or empty: {current_path or 'root'}")
                break

            response.raise_for_status()
            check_rate_limit_remaining(response)
            tree_items = response.json()

            if not tree_items:
                break

            for item in tree_items:
                item_name = item.get("name", "")
                item_type = item.get("type", "")
                item_path = item.get("path", "")

                # If it's a manifest file, add it to results
                if item_type == "blob" and item_name in manifest_files:
                    found_files.append(
                        {
                            "name": item_name,
                            "path": item_path,
                            "type": item.get("mode", ""),
                            "id": item.get("id", ""),
                        }
                    )
                    logger.debug(f"Found manifest file: {item_path}")

                # If it's a directory, push to queue
                elif item_type == "tree":
                    paths_to_search.append(item_path)

            # Check for next page
            next_page = response.headers.get("x-next-page")
            if not next_page:
                break

            params["page"] = int(next_page)

    logger.debug(
        f"Found {len(found_files)} dependency manifest files in project ID {project_id}"
    )
    return found_files


def transform_dependency_files(
    raw_dependency_files: list[dict[str, Any]],
    project_url: str,
) -> list[dict[str, Any]]:
    """
    Transform raw GitLab dependency file data to match our schema.
    """
    transformed = []

    for dep_file in raw_dependency_files:
        file_path = dep_file.get("path", "")
        filename = dep_file.get("name", "")

        dep_file_id = f"{project_url}/blob/{file_path}"

        transformed_file = {
            "id": dep_file_id,
            "path": file_path,
            "filename": filename,
            "project_url": project_url,
        }
        transformed.append(transformed_file)

    logger.info(f"Transformed {len(transformed)} dependency files")
    return transformed


@timeit
def load_dependency_files(
    neo4j_session: neo4j.Session,
    dependency_files: list[dict[str, Any]],
    project_url: str,
    update_tag: int,
) -> None:
    """
    Load GitLab dependency files into the graph for a specific project.
    """
    logger.info(
        f"Loading {len(dependency_files)} dependency files for project {project_url}"
    )
    load(
        neo4j_session,
        GitLabDependencyFileSchema(),
        dependency_files,
        lastupdated=update_tag,
        project_url=project_url,
    )


@timeit
def cleanup_dependency_files(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    project_url: str,
) -> None:
    """
    Remove stale GitLab dependency files from the graph for a specific project.
    """
    logger.info(f"Running GitLab dependency files cleanup for project {project_url}")
    cleanup_params = {**common_job_parameters, "project_url": project_url}
    GraphJob.from_node_schema(GitLabDependencyFileSchema(), cleanup_params).run(
        neo4j_session
    )


@timeit
def sync_gitlab_dependency_files(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    token: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    projects: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """
    Sync GitLab dependency files for all projects.

    Returns a dict mapping project_url to transformed dependency files for use
    by downstream sync functions (e.g., dependencies sync) to avoid duplicate API calls.

    :param neo4j_session: Neo4j session.
    :param gitlab_url: The GitLab instance URL.
    :param token: The GitLab API token.
    :param update_tag: Update tag for tracking data freshness.
    :param common_job_parameters: Common job parameters.
    :param projects: List of project dicts to sync.
    :return: Dict mapping project_url to list of transformed dependency files.
    """
    logger.info(f"Syncing GitLab dependency files for {len(projects)} projects")

    # Store dependency files per project to avoid re-fetching in dependencies sync
    dependency_files_by_project: dict[str, list[dict[str, Any]]] = {}

    # Sync dependency files for each project
    for project in projects:
        project_id: int = project["id"]
        project_name: str = project["name"]
        project_url: str = project["web_url"]

        logger.debug(f"Syncing dependency files for project: {project_name}")

        raw_dependency_files = get_dependency_files(gitlab_url, token, project_id)

        if not raw_dependency_files:
            logger.debug(f"No dependency files found for project {project_name}")
            dependency_files_by_project[project_url] = []
            continue

        transformed_files = transform_dependency_files(
            raw_dependency_files, project_url
        )

        # Store for downstream use
        dependency_files_by_project[project_url] = transformed_files

        logger.debug(
            f"Found {len(transformed_files)} dependency files in project {project_name}"
        )

        load_dependency_files(neo4j_session, transformed_files, project_url, update_tag)

    logger.info("GitLab dependency files sync completed")
    return dependency_files_by_project
