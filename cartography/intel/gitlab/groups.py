"""
GitLab Groups Intelligence Module

This module handles syncing of GitLab groups (nested subgroups within organizations).
Root-level groups (organizations) are handled by the organizations module.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gitlab.organizations import get_organization
from cartography.intel.gitlab.util import get_paginated
from cartography.models.gitlab.groups import GitLabGroupSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_groups(gitlab_url: str, token: str, org_id: int) -> list[dict[str, Any]]:
    """
    Fetch all descendant groups for a specific organization from GitLab.
    """
    logger.info(f"Fetching groups for organization ID {org_id}")
    groups = get_paginated(
        gitlab_url, token, f"/api/v4/groups/{org_id}/descendant_groups"
    )
    logger.info(f"Fetched {len(groups)} groups for organization ID {org_id}")
    return groups


def transform_groups(
    raw_groups: list[dict[str, Any]], org_url: str
) -> list[dict[str, Any]]:
    """
    Transform raw GitLab group data to match our schema.
    """
    transformed = []

    # Build lookup map for parent URL resolution
    id_to_web_url = {group.get("id"): group.get("web_url") for group in raw_groups}

    for group in raw_groups:
        parent_id = group.get("parent_id")
        web_url = group.get("web_url")

        # Get parent group URL if this is a nested group
        parent_group_url = id_to_web_url.get(parent_id) if parent_id else None

        transformed_group = {
            "web_url": web_url,
            "name": group.get("name"),
            "path": group.get("path"),
            "full_path": group.get("full_path"),
            "description": group.get("description"),
            "visibility": group.get("visibility"),
            "parent_id": parent_id,
            "created_at": group.get("created_at"),
            "org_url": org_url,
            "parent_group_url": parent_group_url,
        }
        transformed.append(transformed_group)

    logger.info(f"Transformed {len(transformed)} groups")
    return transformed


@timeit
def load_groups(
    neo4j_session: neo4j.Session,
    groups: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    """
    Load GitLab groups into the graph for a specific organization.
    """
    logger.info(f"Loading {len(groups)} groups for organization {org_url}")
    load(
        neo4j_session,
        GitLabGroupSchema(),
        groups,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def cleanup_groups(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    org_url: str,
) -> None:
    """
    Remove stale GitLab groups from the graph for a specific organization.
    Uses cascade delete to also remove child projects and nested groups.
    """
    logger.info(f"Running GitLab groups cleanup for organization {org_url}")
    cleanup_params = {**common_job_parameters, "org_url": org_url}
    GraphJob.from_node_schema(
        GitLabGroupSchema(), cleanup_params, cascade_delete=True
    ).run(neo4j_session)


@timeit
def sync_gitlab_groups(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    token: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync GitLab groups for a specific organization.

    The organization ID should be passed in common_job_parameters["ORGANIZATION_ID"].
    """
    organization_id = common_job_parameters.get("ORGANIZATION_ID")
    if not organization_id:
        raise ValueError("ORGANIZATION_ID must be provided in common_job_parameters")

    logger.info(f"Syncing GitLab groups for organization {organization_id}")

    # Fetch the organization to get its URL
    org = get_organization(gitlab_url, token, organization_id)
    org_url: str = org["web_url"]
    org_name: str = org["name"]

    logger.info(f"Syncing groups for organization: {org_name} ({org_url})")

    # Fetch groups for this organization
    raw_groups = get_groups(gitlab_url, token, organization_id)

    if not raw_groups:
        logger.info(f"No groups found for organization {org_url}")
        return

    # Transform to match our schema
    transformed_groups = transform_groups(raw_groups, org_url)

    # Load into Neo4j
    load_groups(neo4j_session, transformed_groups, org_url, update_tag)

    logger.info("GitLab groups sync completed")
