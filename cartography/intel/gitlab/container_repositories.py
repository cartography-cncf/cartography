"""
GitLab Container Repositories Intelligence Module

Syncs container registry repositories from GitLab into the graph.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gitlab.util import get_paginated
from cartography.models.gitlab.container_repositories import (
    GitLabContainerRepositorySchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_container_repositories(
    gitlab_url: str,
    token: str,
    group_id: int,
) -> list[dict[str, Any]]:
    """
    Fetch all container registry repositories for a group (including subgroups).

    Uses the group-level registry API to get all repositories across all projects
    in the organization.
    """
    logger.info(f"Fetching container repositories for group ID {group_id}")
    repositories = get_paginated(
        gitlab_url,
        token,
        f"/api/v4/groups/{group_id}/registry/repositories",
    )
    logger.info(
        f"Fetched {len(repositories)} container repositories for group ID {group_id}"
    )
    return repositories


def transform_container_repositories(
    raw_repositories: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Transform raw GitLab container repository data into the format expected by the schema.
    """
    transformed = []
    for repo in raw_repositories:
        transformed.append(
            {
                "location": repo.get("location"),
                "name": repo.get("name"),
                "path": repo.get("path"),
                "id": repo.get("id"),
                "project_id": repo.get("project_id"),
                "created_at": repo.get("created_at"),
                "cleanup_policy_started_at": repo.get("cleanup_policy_started_at"),
                "tags_count": repo.get("tags_count"),
                "size": repo.get("size"),
                "status": repo.get("status"),
            }
        )
    logger.info(f"Transformed {len(transformed)} container repositories")
    return transformed


@timeit
def load_container_repositories(
    neo4j_session: neo4j.Session,
    repositories: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    """
    Load GitLab container repositories into the graph.
    """
    logger.debug(f"Loading {len(repositories)} container repositories for {org_url}")
    load(
        neo4j_session,
        GitLabContainerRepositorySchema(),
        repositories,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def cleanup_container_repositories(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove stale GitLab container repositories from the graph.
    """
    logger.debug("Running GitLab container repositories cleanup")
    GraphJob.from_node_schema(
        GitLabContainerRepositorySchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_container_repositories(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    token: str,
    org_url: str,
    group_id: int,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Sync GitLab container repositories for an organization.
    """
    logger.info(f"Syncing container repositories for organization {org_url}")

    raw_repositories = get_container_repositories(gitlab_url, token, group_id)

    transformed = transform_container_repositories(raw_repositories)
    load_container_repositories(neo4j_session, transformed, org_url, update_tag)
    cleanup_container_repositories(neo4j_session, common_job_parameters)

    return raw_repositories
