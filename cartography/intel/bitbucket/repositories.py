"""
Bitbucket Cloud Repositories Intelligence Module
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.bitbucket.auth import BitbucketCredential
from cartography.intel.bitbucket.util import get_paginated
from cartography.intel.bitbucket.util import strip_uuid
from cartography.models.bitbucket.repositories import BitbucketRepositorySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_repositories(
    credential: BitbucketCredential,
    workspace_slug: str,
) -> list[dict[str, Any]]:
    return get_paginated(credential, f"/repositories/{workspace_slug}")


def _clone_url(repo: dict[str, Any], protocol: str) -> str | None:
    for clone_link in repo.get("links", {}).get("clone", []):
        if clone_link.get("name") == protocol:
            href = clone_link.get("href")
            return href if isinstance(href, str) else None
    return None


def transform_repositories(raw_repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for repo in raw_repos:
        project = repo.get("project")
        record = {
            "id": strip_uuid(repo["uuid"]),
            "full_name": repo["full_name"],
            "slug": repo["slug"],
            "name": repo.get("name"),
            "description": repo.get("description"),
            "is_private": repo.get("is_private"),
            "scm": repo.get("scm"),
            "mainbranch_name": (repo.get("mainbranch") or {}).get("name"),
            "created_on": repo.get("created_on"),
            "updated_on": repo.get("updated_on"),
            "size": repo.get("size"),
            "language": repo.get("language"),
            "clone_https": _clone_url(repo, "https"),
            "clone_ssh": _clone_url(repo, "ssh"),
            "link_html": repo.get("links", {}).get("html", {}).get("href"),
        }
        # Only set project fields when the repo actually has a project, so the
        # CONTAINS relationship is skipped for project-less repos.
        if project:
            record["project_key"] = project.get("key")
            record["project_id"] = strip_uuid(project["uuid"])
        result.append(record)
    return result


@timeit
def load_repositories(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        BitbucketRepositorySchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup_repositories(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    workspace_id: str,
) -> None:
    cleanup_params = {**common_job_parameters, "WORKSPACE_ID": workspace_id}
    GraphJob.from_node_schema(BitbucketRepositorySchema(), cleanup_params).run(
        neo4j_session
    )


@timeit
def sync_bitbucket_repositories(
    neo4j_session: neo4j.Session,
    credential: BitbucketCredential,
    update_tag: int,
    workspaces: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Sync repositories for every given workspace. Returns all transformed repositories."""
    all_repositories: list[dict[str, Any]] = []
    for workspace in workspaces:
        logger.info(
            "Syncing Bitbucket repositories for workspace %s", workspace["slug"]
        )
        raw_repos = get_repositories(credential, workspace["slug"])
        transformed = transform_repositories(raw_repos)
        load_repositories(neo4j_session, transformed, workspace["id"], update_tag)
        all_repositories.extend(transformed)
    return all_repositories
