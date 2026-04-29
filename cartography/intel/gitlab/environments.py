"""
GitLab Environments Intelligence Module

Ingests GitLab environments per project and links each environment to the
CI/CD variables that apply to it. The match logic mirrors GitLab's runtime
behaviour: a variable applies to an environment when its `environment_scope`
matches the environment's name exactly OR is the wildcard `*`.

Glob patterns like `production/*` are recognised by GitLab at runtime but are
not matched here — only exact + wildcard. Glob support can be added later if
demand emerges.
"""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.gitlab.util import get_paginated
from cartography.models.gitlab.environments import (
    GitLabEnvironmentToCIVariableMatchLink,
)
from cartography.models.gitlab.environments import GitLabEnvironmentSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_environments(
    gitlab_url: str,
    token: str,
    project_id: int,
) -> list[dict[str, Any]]:
    """
    Fetch all environments for a project. A 403 returns []; other errors
    propagate.
    """
    try:
        return get_paginated(
            gitlab_url, token, f"/api/v4/projects/{project_id}/environments"
        )
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 403:
            logger.warning(
                "Token lacks permission to read environments for project %s. Skipping.",
                project_id,
            )
            return []
        raise


def transform_environments(
    raw_environments: list[dict[str, Any]],
    project_id: int,
    gitlab_url: str,
) -> list[dict[str, Any]]:
    """
    Transform raw environment data. Pure: no I/O.

    The composite `id` includes `project_id` because GitLab's environment
    IDs are unique per-project, not globally.
    """
    transformed = []
    for env in raw_environments:
        gitlab_env_id = env.get("id")
        if gitlab_env_id is None:
            continue
        transformed.append(
            {
                "id": f"{project_id}:{gitlab_env_id}",
                "gitlab_id": gitlab_env_id,
                "name": env.get("name"),
                "slug": env.get("slug"),
                "external_url": env.get("external_url"),
                "state": env.get("state"),
                "tier": env.get("tier"),
                "created_at": env.get("created_at"),
                "updated_at": env.get("updated_at"),
                "auto_stop_at": env.get("auto_stop_at"),
                "project_id": project_id,
                "gitlab_url": gitlab_url,
            }
        )
    return transformed


def compute_env_variable_links(
    environments: list[dict[str, Any]],
    project_variables: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    For each environment, find the variables that apply to it. A variable
    applies if its `environment_scope` is the wildcard `*` OR an exact match
    for the environment's name.

    Pure: no I/O. Returns a list of `{env_id, variable_id}` records ready for
    `load_matchlinks`.
    """
    links: list[dict[str, Any]] = []
    for env in environments:
        env_name = env.get("name")
        env_id = env.get("id")
        if env_name is None or env_id is None:
            continue
        for variable in project_variables:
            scope = variable.get("environment_scope")
            if scope == "*" or scope == env_name:
                links.append({"env_id": env_id, "variable_id": variable["id"]})
    return links


@timeit
def load_environments(
    neo4j_session: neo4j.Session,
    environments: list[dict[str, Any]],
    project_id: int,
    gitlab_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GitLabEnvironmentSchema(),
        environments,
        lastupdated=update_tag,
        project_id=project_id,
        gitlab_url=gitlab_url,
    )


@timeit
def load_environment_variable_links(
    neo4j_session: neo4j.Session,
    links: list[dict[str, Any]],
    project_id: int,
    gitlab_url: str,
    update_tag: int,
) -> None:
    if not links:
        return
    load_matchlinks(
        neo4j_session,
        GitLabEnvironmentToCIVariableMatchLink(),
        links,
        lastupdated=update_tag,
        _sub_resource_label="GitLabProject",
        _sub_resource_id=project_id,
        gitlab_url=gitlab_url,
    )


@timeit
def cleanup_environments(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    project_id: int,
    gitlab_url: str,
) -> None:
    cleanup_params = {
        **common_job_parameters,
        "project_id": project_id,
        "gitlab_url": gitlab_url,
    }
    GraphJob.from_node_schema(GitLabEnvironmentSchema(), cleanup_params).run(
        neo4j_session
    )


@timeit
def sync_gitlab_environments(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    token: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    projects: list[dict[str, Any]],
    variables_by_project: dict[int, list[dict[str, Any]]],
) -> None:
    """
    Sync environments for each project, then link each environment to the
    project-level CI/CD variables that apply to it.
    """
    logger.info("Syncing GitLab environments for %d projects", len(projects))

    for project in projects:
        project_id: int = project["id"]
        raw = get_environments(gitlab_url, token, project_id)
        if not raw:
            continue
        transformed = transform_environments(raw, project_id, gitlab_url)
        load_environments(
            neo4j_session, transformed, project_id, gitlab_url, update_tag
        )

        project_variables = variables_by_project.get(project_id, [])
        links = compute_env_variable_links(transformed, project_variables)
        load_environment_variable_links(
            neo4j_session, links, project_id, gitlab_url, update_tag
        )

    logger.info("GitLab environments sync completed")
