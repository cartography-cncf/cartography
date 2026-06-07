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
from cartography.graph.job import GraphJob
from cartography.intel.gitlab.util import get_paginated
from cartography.models.gitlab.environments import GitLabEnvironmentSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_environments(
    gitlab_url: str,
    token: str,
    project_id: int,
) -> list[dict[str, Any]] | None:
    """
    Fetch all environments for a project. Returns:
    - the list on success
    - ``None`` on 403 (permission-denied) so the caller can skip BOTH the
      load and the cleanup for that project; an empty list would otherwise
      look like a successful empty sync and trigger cleanup that deletes
      every previously-ingested environment.
    - ``[]`` on 404 (project has no environments feature enabled / project
      removed since `all_projects` was fetched). 404 is non-fatal and does
      not need to skip cleanup — the project legitimately has no envs.
    Other errors propagate.
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
            return None
        if e.response is not None and e.response.status_code == 404:
            logger.warning(
                "Environments endpoint returned 404 for project %s. Skipping.",
                project_id,
            )
            return []
        raise


def _matching_variable_ids(
    env_name: str,
    project_variables: list[dict[str, Any]],
) -> list[str]:
    """Variable IDs whose ``environment_scope`` matches this env (exact or ``*``)."""
    return [
        v["id"]
        for v in project_variables
        if v.get("environment_scope") in ("*", env_name)
    ]


def transform_environments(
    raw_environments: list[dict[str, Any]],
    project_id: int,
    gitlab_url: str,
    project_variables: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    Transform raw environment data. Pure: no I/O.

    The composite ``id`` includes ``project_id`` because GitLab's environment
    IDs are unique per-project, not globally.

    Each record carries a ``linked_variable_ids`` list — the IDs of the
    project-level CI variables whose ``environment_scope`` matches this
    environment (exact name match OR wildcard ``*``). Used by the
    ``HAS_CI_VARIABLE`` other_relationship at load time.
    """
    project_variables = project_variables or []
    transformed = []
    for env in raw_environments:
        gitlab_env_id = env.get("id")
        if gitlab_env_id is None:
            continue
        env_name = env.get("name")
        # Variable matching only happens when the environment has a name —
        # an env with no name cannot match an `environment_scope`. We still
        # ingest the node itself so it appears in the graph.
        linked_variable_ids = (
            _matching_variable_ids(env_name, project_variables)
            if env_name is not None
            else []
        )
        transformed.append(
            {
                "id": f"{project_id}:{gitlab_env_id}",
                "gitlab_id": gitlab_env_id,
                "name": env_name,
                "slug": env.get("slug"),
                "external_url": env.get("external_url"),
                "state": env.get("state"),
                "tier": env.get("tier"),
                "created_at": env.get("created_at"),
                "updated_at": env.get("updated_at"),
                "auto_stop_at": env.get("auto_stop_at"),
                "project_id": project_id,
                "gitlab_url": gitlab_url,
                "linked_variable_ids": linked_variable_ids,
            }
        )
    return transformed


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
    skip_projects: set[int] | None = None,
) -> set[int]:
    """
    Sync environments for each project, then link each environment to the
    project-level CI/CD variables that apply to it.

    ``skip_projects`` lists project IDs whose CI variables could not be
    loaded this run. Those projects are skipped entirely — refreshing
    environments with no ``linked_variable_ids`` would let cleanup wipe
    the ``HAS_CI_VARIABLE`` edges from existing envs even though the
    variables themselves were preserved upstream.

    Returns the union of ``skip_projects`` and the projects skipped due
    to a 403 on the environments endpoint, so the caller can avoid
    running cleanup for any of them.
    """
    logger.info("Syncing GitLab environments for %d projects", len(projects))
    skip_projects = skip_projects or set()
    skipped_projects: set[int] = set(skip_projects)

    for project in projects:
        project_id: int = project["id"]
        if project_id in skip_projects:
            continue
        raw = get_environments(gitlab_url, token, project_id)
        if raw is None:
            skipped_projects.add(project_id)
            continue
        if not raw:
            continue
        project_variables = variables_by_project.get(project_id, [])
        transformed = transform_environments(
            raw, project_id, gitlab_url, project_variables
        )
        load_environments(
            neo4j_session, transformed, project_id, gitlab_url, update_tag
        )

    logger.info("GitLab environments sync completed")
    return skipped_projects
