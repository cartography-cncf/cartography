"""
GitLab Terraform States Intelligence Module

Discovers Terraform HTTP backend states managed by GitLab.

GitLab has no REST list endpoint for terraform states. The only way to list
them is via GraphQL:
  POST /api/graphql
  query { project(fullPath: "...") { terraformStates { nodes { ... } } } }

Reference: https://gitlab.com/gitlab-org/api/client-go/-/blob/main/terraform_states.go
"""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gitlab.terraform_states import GitLabTerraformStateSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_TERRAFORM_STATES_QUERY = """
query($fullPath: ID!) {
  project(fullPath: $fullPath) {
    terraformStates {
      nodes {
        name
        createdAt
        updatedAt
        deletedAt
        lockedAt
        latestVersion {
          serial
          createdAt
          updatedAt
        }
      }
    }
  }
}
"""


def get_terraform_states(
    gitlab_url: str, token: str, project_path: str
) -> list[dict[str, Any]]:
    """
    List terraform states for a project via GitLab GraphQL API.

    The REST endpoint GET /api/v4/projects/:id/terraform/state/:name fetches
    a *specific* named state and has no list variant. GraphQL is the only
    supported way to enumerate states.
    """
    response = requests.post(
        f"{gitlab_url}/api/graphql",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "query": _TERRAFORM_STATES_QUERY,
            "variables": {"fullPath": project_path},
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    errors = data.get("errors")
    if errors:
        logger.warning(
            "GraphQL errors fetching terraform states for %s: %s", project_path, errors
        )
        return []

    project = (data.get("data") or {}).get("project")
    if not project:
        logger.debug("No project found in GraphQL response for path %s", project_path)
        return []

    return project.get("terraformStates", {}).get("nodes", [])


def transform_terraform_states(
    raw_states: list[dict[str, Any]],
    project_id: int,
    gitlab_url: str,
) -> list[dict[str, Any]]:
    transformed = []
    for state in raw_states:
        if state.get("deletedAt"):
            continue
        latest = state.get("latestVersion") or {}
        transformed.append(
            {
                "id": f"{project_id}/{state['name']}",
                "name": state["name"],
                "project_id": project_id,
                "locked": state.get("lockedAt") is not None,
                "locked_at": state.get("lockedAt"),
                "locked_by_user_id": None,  # not available via GraphQL list query
                "updated_at": state.get("updatedAt"),
                "latest_version_serial": latest.get("serial"),
                "latest_version_created_at": latest.get("createdAt"),
                "latest_version_created_by_user_id": None,  # not available via GraphQL list query
                "latest_version_job_id": None,  # not available via GraphQL list query
                "latest_version_pipeline_id": None,  # not available via GraphQL list query
                "gitlab_url": gitlab_url,
                "state_url": f"{gitlab_url}/api/v4/projects/{project_id}/terraform/state/{state['name']}",
            }
        )
    return transformed


@timeit
def load_terraform_states(
    neo4j_session: neo4j.Session,
    states: list[dict[str, Any]],
    project_id: int,
    gitlab_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GitLabTerraformStateSchema(),
        states,
        lastupdated=update_tag,
        project_id=project_id,
        gitlab_url=gitlab_url,
    )


@timeit
def cleanup_terraform_states(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    project_id: int,
    gitlab_url: str,
) -> None:
    GraphJob.from_node_schema(
        GitLabTerraformStateSchema(),
        {
            **common_job_parameters,
            "project_id": project_id,
            "gitlab_url": gitlab_url,
        },
    ).run(neo4j_session)


@timeit
def sync_gitlab_terraform_states(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    token: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    all_projects: list[dict[str, Any]],
) -> list[int]:
    """
    Sync Terraform states for all projects. Returns list of project IDs that had states.
    """
    projects_with_states: list[int] = []
    for project in all_projects:
        project_id: int = project["id"]
        project_path: str = project.get("path_with_namespace", "")
        if not project_path:
            logger.warning(
                "Skipping project %s: missing path_with_namespace", project_id
            )
            continue
        try:
            raw = get_terraform_states(gitlab_url, token, project_path)
        except Exception as e:
            logger.warning(
                "Failed to fetch Terraform states for project %s (%s): %s",
                project_path,
                project_id,
                e,
            )
            continue
        if not raw:
            continue
        states = transform_terraform_states(raw, project_id, gitlab_url)
        load_terraform_states(neo4j_session, states, project_id, gitlab_url, update_tag)
        projects_with_states.append(project_id)

    logger.info(
        "Synced Terraform states for %d/%d projects",
        len(projects_with_states),
        len(all_projects),
    )
    return projects_with_states
