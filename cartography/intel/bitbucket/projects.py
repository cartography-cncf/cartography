"""
Bitbucket Cloud Projects Intelligence Module
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.bitbucket.auth import BitbucketCredential
from cartography.intel.bitbucket.util import get_paginated
from cartography.intel.bitbucket.util import strip_uuid
from cartography.models.bitbucket.projects import BitbucketProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_projects(
    credential: BitbucketCredential,
    workspace_slug: str,
) -> list[dict[str, Any]]:
    return get_paginated(credential, f"/workspaces/{workspace_slug}/projects")


def transform_projects(raw_projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for project in raw_projects:
        result.append(
            {
                "id": strip_uuid(project["uuid"]),
                "key": project["key"],
                "name": project.get("name"),
                "description": project.get("description"),
                "is_private": project.get("is_private"),
                "created_on": project.get("created_on"),
                "updated_on": project.get("updated_on"),
                "link_html": project.get("links", {}).get("html", {}).get("href"),
            },
        )
    return result


@timeit
def load_projects(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        BitbucketProjectSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup_projects(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    workspace_id: str,
) -> None:
    cleanup_params = {**common_job_parameters, "WORKSPACE_ID": workspace_id}
    GraphJob.from_node_schema(BitbucketProjectSchema(), cleanup_params).run(
        neo4j_session
    )


@timeit
def sync_bitbucket_projects(
    neo4j_session: neo4j.Session,
    credential: BitbucketCredential,
    update_tag: int,
    workspaces: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Sync projects for every given workspace. Returns all transformed projects."""
    all_projects: list[dict[str, Any]] = []
    for workspace in workspaces:
        logger.info("Syncing Bitbucket projects for workspace %s", workspace["slug"])
        raw_projects = get_projects(credential, workspace["slug"])
        transformed = transform_projects(raw_projects)
        load_projects(neo4j_session, transformed, workspace["id"], update_tag)
        all_projects.extend(transformed)
    return all_projects
