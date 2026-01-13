"""
GitLab Organizations Intelligence Module
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gitlab.util import get_single
from cartography.models.gitlab.organizations import GitLabOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_organization(gitlab_url: str, token: str, org_id: int) -> dict[str, Any]:
    """
    Fetch a specific top-level group (organization) from GitLab by ID.
    """
    logger.info(f"Fetching organization ID {org_id} from {gitlab_url}")
    return get_single(gitlab_url, token, f"/api/v4/groups/{org_id}")


def transform_organizations(
    raw_orgs: list[dict[str, Any]], gitlab_url: str
) -> list[dict[str, Any]]:
    """
    Transform raw GitLab organization data to match our schema.
    """
    transformed = []

    for org in raw_orgs:
        transformed_org = {
            "web_url": org.get("web_url"),
            "name": org.get("name"),
            "path": org.get("path"),
            "full_path": org.get("full_path"),
            "description": org.get("description"),
            "visibility": org.get("visibility"),
            "created_at": org.get("created_at"),
            "gitlab_url": gitlab_url,  # Track which instance this org belongs to
        }
        transformed.append(transformed_org)

    logger.info(f"Transformed {len(transformed)} organizations")
    return transformed


@timeit
def load_organizations(
    neo4j_session: neo4j.Session,
    organizations: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load GitLab organizations into the graph.
    """
    logger.info(f"Loading {len(organizations)} organizations")
    load(
        neo4j_session,
        GitLabOrganizationSchema(),
        organizations,
        lastupdated=update_tag,
    )


@timeit
def cleanup_organizations(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    gitlab_url: str,
) -> None:
    """
    Remove stale GitLab organizations from the graph for a specific GitLab instance.
    """
    logger.info(f"Running GitLab organizations cleanup for {gitlab_url}")
    cleanup_params = {**common_job_parameters, "gitlab_url": gitlab_url}
    GraphJob.from_node_schema(GitLabOrganizationSchema(), cleanup_params).run(
        neo4j_session
    )


@timeit
def sync_gitlab_organizations(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    token: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> dict[str, Any]:
    """
    Sync a specific GitLab organization (top-level group) by ID.

    The organization ID should be passed in common_job_parameters["ORGANIZATION_ID"].
    Returns the organization data for use by downstream sync functions.
    """
    organization_id = common_job_parameters.get("ORGANIZATION_ID")
    if not organization_id:
        raise ValueError("ORGANIZATION_ID must be provided in common_job_parameters")

    logger.info(f"Syncing GitLab organization ID {organization_id}")

    # get_organization raises HTTPError on 404, so no need to check for empty response
    raw_org = get_organization(gitlab_url, token, organization_id)

    transformed_orgs = transform_organizations([raw_org], gitlab_url)

    load_organizations(neo4j_session, transformed_orgs, update_tag)

    logger.info(f"GitLab organization sync completed for {raw_org.get('name')}")

    return raw_org
