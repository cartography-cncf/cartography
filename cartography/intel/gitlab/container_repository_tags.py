"""
GitLab Container Repository Tags Intelligence Module

Syncs container registry tags from GitLab into the graph.
Tags are fetched per-repository and reference container images by digest.
"""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gitlab.util import get_paginated
from cartography.intel.gitlab.util import get_single
from cartography.models.gitlab.container_repository_tags import (
    GitLabContainerRepositoryTagSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_container_repository_tags(
    gitlab_url: str,
    token: str,
    project_id: int,
    repository_id: int,
) -> list[dict[str, Any]]:
    """
    Fetch all tags for a specific container repository with full details.

    The tag list endpoint doesn't include digests, so we fetch details for each tag.
    """
    logger.debug(
        f"Fetching tags for repository {repository_id} in project {project_id}"
    )

    # Get tag list (doesn't include digest)
    tags = get_paginated(
        gitlab_url,
        token,
        f"/api/v4/projects/{project_id}/registry/repositories/{repository_id}/tags",
    )

    # Fetch full details for each tag to get the digest
    detailed_tags = []
    for tag in tags:
        tag_name = tag.get("name")
        if not tag_name:
            continue

        try:
            tag_detail = get_single(
                gitlab_url,
                token,
                f"/api/v4/projects/{project_id}/registry/repositories/{repository_id}/tags/{tag_name}",
            )
            detailed_tags.append(tag_detail)
        except requests.exceptions.HTTPError as e:
            logger.warning(
                f"Failed to fetch details for tag {tag_name} after retries: {e}"
            )
            detailed_tags.append(tag)  # Fall back to basic info

    return detailed_tags


def get_all_container_repository_tags(
    gitlab_url: str,
    token: str,
    repositories: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Fetch tags for all container repositories.
    """
    all_tags = []
    for repo in repositories:
        project_id = repo.get("project_id")
        repository_id = repo.get("id")
        repository_location = repo.get("location")
        if not project_id or not repository_id:
            logger.warning(f"Repository missing project_id or id: {repo}")
            continue

        tags = get_container_repository_tags(
            gitlab_url, token, project_id, repository_id
        )
        # Attach the repository location to each tag for the HAS_TAG relationship
        for tag in tags:
            tag["_repository_location"] = repository_location
        all_tags.extend(tags)

    logger.info(f"Fetched {len(all_tags)} tags across {len(repositories)} repositories")
    return all_tags


def transform_container_repository_tags(
    raw_tags: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Transform raw GitLab tag data into the format expected by the schema.
    """
    transformed = []
    for tag in raw_tags:
        transformed.append(
            {
                "location": tag.get("location"),
                "name": tag.get("name"),
                "path": tag.get("path"),
                "repository_location": tag.get("_repository_location"),
                "revision": tag.get("revision"),
                "short_revision": tag.get("short_revision"),
                "digest": tag.get("digest"),
                "created_at": tag.get("created_at"),
                "total_size": tag.get("total_size"),
            }
        )
    logger.info(f"Transformed {len(transformed)} container repository tags")
    return transformed


@timeit
def load_container_repository_tags(
    neo4j_session: neo4j.Session,
    tags: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    """
    Load GitLab container repository tags into the graph.
    """
    logger.info(f"Loading {len(tags)} container repository tags for {org_url}")
    load(
        neo4j_session,
        GitLabContainerRepositoryTagSchema(),
        tags,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def cleanup_container_repository_tags(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove stale GitLab container repository tags from the graph.
    """
    logger.info("Running GitLab container repository tags cleanup")
    GraphJob.from_node_schema(
        GitLabContainerRepositoryTagSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_container_repository_tags(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    token: str,
    org_url: str,
    repositories: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Sync GitLab container repository tags for an organization.
    """
    logger.info(f"Syncing container repository tags for organization {org_url}")

    raw_tags = get_all_container_repository_tags(gitlab_url, token, repositories)

    transformed = transform_container_repository_tags(raw_tags)
    load_container_repository_tags(neo4j_session, transformed, org_url, update_tag)
    cleanup_container_repository_tags(neo4j_session, common_job_parameters)

    return raw_tags
