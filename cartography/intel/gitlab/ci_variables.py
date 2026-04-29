"""
GitLab CI/CD Variables Intelligence Module

Ingests GitLab CI/CD variables at two scopes:
- group-level (`/api/v4/groups/:id/variables`)
- project-level (`/api/v4/projects/:id/variables`)

The variable's `value` is NEVER stored. Only metadata
(key, variable_type, protected, masked, environment_scope, ...) is ingested,
matching the GitHub Actions secrets/variables convention.

Tokens that lack permission to read variables for a given scope (403) are
tolerated: a warning is logged and the scope is skipped.

`sync_gitlab_ci_variables` returns a `dict[project_id -> list[variables]]`
that downstream modules (environments, ci_config) can use to build
MatchLinks without re-querying Neo4j.
"""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gitlab.util import get_paginated
from cartography.models.gitlab.ci_variables import GitLabGroupCIVariableSchema
from cartography.models.gitlab.ci_variables import GitLabProjectCIVariableSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _make_variable_id(
    scope_type: str,
    scope_id: int,
    key: str,
    environment_scope: str,
) -> str:
    """
    Build a stable composite ID for a CI/CD variable.

    The same `key` may coexist multiple times within a single scope as long
    as the `environment_scope` differs (GitLab uses `environment_scope` to
    pick which value applies to a given pipeline).
    """
    return f"{scope_type}:{scope_id}:{key}:{environment_scope}"


@timeit
def get_group_variables(
    gitlab_url: str,
    token: str,
    group_id: int,
) -> list[dict[str, Any]]:
    """
    Fetch group-level CI/CD variables. A 403 returns []; other errors propagate.
    """
    try:
        return get_paginated(gitlab_url, token, f"/api/v4/groups/{group_id}/variables")
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 403:
            logger.warning(
                "Token lacks permission to read CI variables for group %s. Skipping.",
                group_id,
            )
            return []
        raise


@timeit
def get_project_variables(
    gitlab_url: str,
    token: str,
    project_id: int,
) -> list[dict[str, Any]]:
    """
    Fetch project-level CI/CD variables. A 403 returns []; other errors propagate.
    """
    try:
        return get_paginated(
            gitlab_url, token, f"/api/v4/projects/{project_id}/variables"
        )
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 403:
            logger.warning(
                "Token lacks permission to read CI variables for project %s. Skipping.",
                project_id,
            )
            return []
        raise


def transform_variables(
    raw_variables: list[dict[str, Any]],
    scope_type: str,
    scope_id: int,
    gitlab_url: str,
) -> list[dict[str, Any]]:
    """
    Transform raw GitLab variable data to match our schema. Pure: no I/O.

    `value` is intentionally dropped — only metadata is stored.
    `environment_scope` defaults to "*" (GitLab's wildcard) when missing.
    """
    transformed = []
    for variable in raw_variables:
        key = variable.get("key")
        if key is None:
            continue
        environment_scope = variable.get("environment_scope") or "*"
        transformed.append(
            {
                "id": _make_variable_id(scope_type, scope_id, key, environment_scope),
                "key": key,
                "variable_type": variable.get("variable_type"),
                "protected": bool(variable.get("protected", False)),
                "masked": bool(variable.get("masked", False)),
                "masked_and_hidden": bool(variable.get("masked_and_hidden", False)),
                "raw": bool(variable.get("raw", False)),
                "environment_scope": environment_scope,
                "description": variable.get("description"),
                "scope_type": scope_type,
                "gitlab_url": gitlab_url,
            }
        )
    return transformed


@timeit
def load_group_variables(
    neo4j_session: neo4j.Session,
    variables: list[dict[str, Any]],
    group_id: int,
    gitlab_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GitLabGroupCIVariableSchema(),
        variables,
        lastupdated=update_tag,
        group_id=group_id,
        gitlab_url=gitlab_url,
    )


@timeit
def load_project_variables(
    neo4j_session: neo4j.Session,
    variables: list[dict[str, Any]],
    project_id: int,
    gitlab_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GitLabProjectCIVariableSchema(),
        variables,
        lastupdated=update_tag,
        project_id=project_id,
        gitlab_url=gitlab_url,
    )


@timeit
def cleanup_group_variables(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    group_id: int,
    gitlab_url: str,
) -> None:
    cleanup_params = {
        **common_job_parameters,
        "group_id": group_id,
        "gitlab_url": gitlab_url,
    }
    GraphJob.from_node_schema(GitLabGroupCIVariableSchema(), cleanup_params).run(
        neo4j_session
    )


@timeit
def cleanup_project_variables(
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
    GraphJob.from_node_schema(GitLabProjectCIVariableSchema(), cleanup_params).run(
        neo4j_session
    )


@timeit
def sync_gitlab_ci_variables(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    token: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    groups: list[dict[str, Any]],
    projects: list[dict[str, Any]],
) -> dict[int, list[dict[str, Any]]]:
    """
    Sync CI/CD variables at group and project scope.

    Returns a `{project_id: [variable, ...]}` map of project-level variables,
    so downstream modules (environments, ci_config) can match without
    re-querying.
    """
    logger.info(
        "Syncing GitLab CI/CD variables for %d groups and %d projects",
        len(groups),
        len(projects),
    )

    for group in groups:
        group_id: int = group["id"]
        raw = get_group_variables(gitlab_url, token, group_id)
        if not raw:
            continue
        transformed = transform_variables(raw, "group", group_id, gitlab_url)
        load_group_variables(
            neo4j_session, transformed, group_id, gitlab_url, update_tag
        )

    project_variables: dict[int, list[dict[str, Any]]] = {}
    for project in projects:
        project_id: int = project["id"]
        raw = get_project_variables(gitlab_url, token, project_id)
        if not raw:
            project_variables[project_id] = []
            continue
        transformed = transform_variables(raw, "project", project_id, gitlab_url)
        load_project_variables(
            neo4j_session, transformed, project_id, gitlab_url, update_tag
        )
        project_variables[project_id] = transformed

    logger.info("GitLab CI/CD variables sync completed")
    return project_variables
