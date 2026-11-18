"""
Bitbucket Cloud Workspaces Intelligence Module
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.intel.bitbucket.auth import BitbucketCredential
from cartography.intel.bitbucket.util import get_single
from cartography.intel.bitbucket.util import strip_uuid
from cartography.models.bitbucket.workspaces import BitbucketWorkspaceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_workspace(credential: BitbucketCredential, slug: str) -> dict[str, Any]:
    """
    Fetch a single named workspace.

    There is no bare "list every workspace I can see" endpoint to fall back
    to - GET /workspaces 404s for every credential type Cartography supports
    (API tokens, Access tokens, and OAuth), even with valid scopes - so a
    known slug is always required.
    """
    return get_single(credential, f"/workspaces/{slug}")


def transform_workspaces(raw_workspaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for workspace in raw_workspaces:
        result.append(
            {
                "id": strip_uuid(workspace["uuid"]),
                "slug": workspace["slug"],
                "name": workspace.get("name"),
                "is_private": workspace.get("is_private"),
                "created_on": workspace.get("created_on"),
                "link_html": workspace.get("links", {}).get("html", {}).get("href"),
            },
        )
    return result


@timeit
def load_workspaces(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        BitbucketWorkspaceSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def sync_bitbucket_workspaces(
    neo4j_session: neo4j.Session,
    credential: BitbucketCredential,
    update_tag: int,
    configured_slugs: list[str],
) -> list[dict[str, Any]]:
    """Sync each configured Bitbucket workspace, fetched directly by slug."""
    logger.info("Syncing Bitbucket workspaces")
    raw_workspaces = [get_workspace(credential, slug) for slug in configured_slugs]
    transformed = transform_workspaces(raw_workspaces)

    load_workspaces(neo4j_session, transformed, update_tag)
    return transformed
