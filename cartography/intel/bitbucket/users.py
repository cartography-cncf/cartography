"""
Bitbucket Cloud Users (workspace members) Intelligence Module
"""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.bitbucket.auth import BitbucketCredential
from cartography.intel.bitbucket.util import get_paginated
from cartography.models.bitbucket.users import BitbucketUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_workspace_members(
    credential: BitbucketCredential,
    workspace_slug: str,
) -> list[dict[str, Any]]:
    return get_paginated(credential, f"/workspaces/{workspace_slug}/members")


def transform_users(raw_members: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for membership in raw_members:
        user = membership["user"]
        result.append(
            {
                "account_id": user["account_id"],
                "uuid": user.get("uuid"),
                "display_name": user.get("display_name"),
                "nickname": user.get("nickname"),
                "avatar_url": user.get("links", {}).get("avatar", {}).get("href"),
                "link_html": user.get("links", {}).get("html", {}).get("href"),
            },
        )
    return result


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        BitbucketUserSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup_users(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    workspace_id: str,
) -> None:
    cleanup_params = {**common_job_parameters, "WORKSPACE_ID": workspace_id}
    GraphJob.from_node_schema(BitbucketUserSchema(), cleanup_params).run(neo4j_session)


@timeit
def sync_bitbucket_users(
    neo4j_session: neo4j.Session,
    credential: BitbucketCredential,
    update_tag: int,
    workspaces: list[dict[str, Any]],
) -> set[str]:
    """
    Sync members for every given workspace.

    Returns the set of workspace IDs whose members could not be listed (e.g. a
    403 from a token/OAuth scope that lacks account:read). When it is not
    empty, the caller skips user cleanup for every workspace, because a user
    shared with an unreadable workspace would otherwise be deleted.
    """
    skipped_workspace_ids: set[str] = set()
    for workspace in workspaces:
        logger.info("Syncing Bitbucket members for workspace %s", workspace["slug"])
        try:
            raw_members = get_workspace_members(credential, workspace["slug"])
        except requests.exceptions.HTTPError as e:
            if e.response is None or e.response.status_code != 403:
                raise
            logger.warning(
                "Credential lacks permission to list members for Bitbucket "
                "workspace %s; skipping its members this run.",
                workspace["slug"],
            )
            skipped_workspace_ids.add(workspace["id"])
            continue
        transformed = transform_users(raw_members)
        load_users(neo4j_session, transformed, workspace["id"], update_tag)
    return skipped_workspace_ids
