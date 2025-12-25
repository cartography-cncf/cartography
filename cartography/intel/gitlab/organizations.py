"""
GitLab Organizations Intelligence Module
"""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gitlab.organizations import GitLabOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_organizations(gitlab_url: str, token: str) -> list[dict[str, Any]]:
    """
    Fetch all top-level groups (organizations) from GitLab using REST API.
    Organizations are groups where parent_id is null.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Use the /groups endpoint with top_level_only=true to get root-level groups
    api_url = f"{gitlab_url}/api/v4/groups"
    params = {
        "per_page": 100,  # Max items per page
        "page": 1,
        "top_level_only": True,  # Only fetch root-level groups (organizations)
    }

    organizations = []

    logger.info(f"Fetching organizations from {gitlab_url}")

    while True:
        response = requests.get(api_url, headers=headers, params=params, timeout=60)
        response.raise_for_status()

        page_orgs = response.json()

        if not page_orgs:
            # No more data
            break

        organizations.extend(page_orgs)

        logger.info(
            f"Fetched {len(page_orgs)} organizations from page {params['page']}"
        )

        # Check if there's a next page
        next_page = response.headers.get("x-next-page")
        if not next_page:
            # No more pages
            break

        params["page"] = int(next_page)

    logger.info(f"Fetched total of {len(organizations)} organizations")
    return organizations


def get_organization(gitlab_url: str, token: str, org_id: int) -> dict[str, Any]:
    """
    Fetch a specific top-level group (organization) from GitLab by ID.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    api_url = f"{gitlab_url}/api/v4/groups/{org_id}"

    logger.info(f"Fetching organization ID {org_id} from {gitlab_url}")

    response = requests.get(api_url, headers=headers, timeout=60)
    response.raise_for_status()

    organization = response.json()
    logger.info(f"Fetched organization: {organization.get('name')}")

    return organization


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
