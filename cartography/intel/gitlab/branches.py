"""
GitLab Branches Intelligence Module
"""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gitlab.branches import GitLabBranchSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_branches(gitlab_url: str, token: str, project_id: int) -> list[dict[str, Any]]:
    """
    Fetch all branches for a specific project from GitLab using REST API.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Use the /projects/:id/repository/branches endpoint to get all branches
    api_url = f"{gitlab_url}/api/v4/projects/{project_id}/repository/branches"
    params = {
        "per_page": 100,  # Max items per page
        "page": 1,
    }

    branches = []

    logger.info(f"Fetching branches for project ID {project_id} from {gitlab_url}")

    while True:
        response = requests.get(api_url, headers=headers, params=params, timeout=60)
        response.raise_for_status()

        page_branches = response.json()

        if not page_branches:
            # No more data
            break

        branches.extend(page_branches)

        logger.info(f"Fetched {len(page_branches)} branches from page {params['page']}")

        # Check if there's a next page
        next_page = response.headers.get("x-next-page")
        if not next_page:
            # No more pages
            break

        params["page"] = int(next_page)

    logger.info(
        f"Fetched total of {len(branches)} branches for project ID {project_id}"
    )
    return branches


def transform_branches(
    raw_branches: list[dict[str, Any]], project_url: str
) -> list[dict[str, Any]]:
    """
    Transform raw GitLab branch data to match our schema.
    """
    transformed = []

    for branch in raw_branches:
        branch_name = branch.get("name")

        # Construct unique ID: project_url + branch_name
        # This ensures branches with the same name in different projects are unique
        branch_id = f"{project_url}/tree/{branch_name}"

        transformed_branch = {
            # Node properties
            "id": branch_id,  # Unique identifier
            "name": branch_name,
            "protected": branch.get("protected", False),
            "default": branch.get("default", False),
            "web_url": branch.get("web_url"),
            # Relationship fields
            "project_url": project_url,  # For RESOURCE relationship to GitLabProject
        }
        transformed.append(transformed_branch)

    logger.info(f"Transformed {len(transformed)} branches")
    return transformed


@timeit
def load_branches(
    neo4j_session: neo4j.Session,
    branches: list[dict[str, Any]],
    project_url: str,
    update_tag: int,
) -> None:
    """
    Load GitLab branches into the graph for a specific project.
    """
    logger.info(f"Loading {len(branches)} branches for project {project_url}")
    load(
        neo4j_session,
        GitLabBranchSchema(),
        branches,
        lastupdated=update_tag,
        project_url=project_url,
    )


@timeit
def cleanup_branches(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    project_url: str,
) -> None:
    """
    Remove stale GitLab branches from the graph for a specific project.
    """
    logger.info(f"Running GitLab branches cleanup for project {project_url}")
    cleanup_params = {**common_job_parameters, "project_url": project_url}
    GraphJob.from_node_schema(GitLabBranchSchema(), cleanup_params).run(neo4j_session)


@timeit
def sync_gitlab_branches(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    token: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    projects: list[dict[str, Any]],
) -> None:
    """
    Sync GitLab branches for all projects.
    """
    logger.info(f"Syncing GitLab branches for {len(projects)} projects")

    # Sync branches for each project
    for project in projects:
        project_id: int = project["id"]
        project_name: str = project["name"]
        project_url: str = project["web_url"]

        logger.info(f"Syncing branches for project: {project_name}")

        # Fetch branches for this project
        raw_branches = get_branches(gitlab_url, token, project_id)

        if not raw_branches:
            logger.info(f"No branches found for project {project_name}")
            continue

        # Transform to match our schema
        transformed_branches = transform_branches(raw_branches, project_url)

        logger.info(
            f"Found {len(transformed_branches)} branches in project {project_name}"
        )

        # Load branches for this project
        load_branches(neo4j_session, transformed_branches, project_url, update_tag)

    logger.info("GitLab branches sync completed")
