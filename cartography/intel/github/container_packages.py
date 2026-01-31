"""
GitHub Container Packages Intelligence Module

Syncs container packages from GitHub Container Registry (GHCR) into the graph.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.github import util
from cartography.models.github.container_packages import GitHubContainerPackageSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_container_packages(
    token: str,
    api_url: str,
    organization: str,
) -> list[dict[str, Any]]:
    """
    Fetch all container packages for a GitHub organization.

    Uses the GitHub Packages API to get all container-type packages.
    See: https://docs.github.com/en/rest/packages/packages#list-packages-for-an-organization
    """
    logger.info(f"Fetching container packages for organization {organization}")

    # GitHub REST API endpoint for listing organization packages
    # We filter by package_type=container to get only GHCR packages
    endpoint = f"/orgs/{organization}/packages?package_type=container"

    # Get the REST API base URL from the GraphQL URL
    base_url = util._get_rest_api_base_url(api_url)

    packages = util.fetch_all_rest_api_pages(
        token,
        base_url,
        endpoint,
        result_key="",  # The endpoint returns a list directly, not wrapped in an object
    )

    logger.info(f"Fetched {len(packages)} container packages for {organization}")
    return packages


def get_package_versions(
    token: str,
    api_url: str,
    organization: str,
    package_name: str,
) -> list[dict[str, Any]]:
    """
    Fetch all versions for a specific container package.

    See: https://docs.github.com/en/rest/packages/packages#list-package-versions-for-a-package-owned-by-an-organization
    """
    logger.debug(f"Fetching versions for package {package_name}")

    endpoint = f"/orgs/{organization}/packages/container/{package_name}/versions"

    # Get the REST API base URL from the GraphQL URL
    base_url = util._get_rest_api_base_url(api_url)

    versions = util.fetch_all_rest_api_pages(
        token,
        base_url,
        endpoint,
        result_key="",  # The endpoint returns a list directly
    )

    logger.debug(f"Fetched {len(versions)} versions for package {package_name}")
    return versions


def transform_container_packages(
    raw_packages: list[dict[str, Any]],
    org_url: str,
) -> list[dict[str, Any]]:
    """
    Transform raw GitHub package data into the format expected by the schema.
    """
    transformed = []
    for package in raw_packages:
        # Extract repository information if available
        repository = package.get("repository")
        repository_id = repository.get("id") if repository else None
        repository_name = repository.get("full_name") if repository else None

        # Extract owner information
        owner = package.get("owner", {})
        owner_login = owner.get("login")
        owner_type = owner.get("type")

        transformed.append(
            {
                "id": package.get("id"),
                "name": package.get("name"),
                "package_type": package.get("package_type"),
                "visibility": package.get("visibility"),
                "url": package.get("url"),
                "html_url": package.get("html_url"),
                "created_at": package.get("created_at"),
                "updated_at": package.get("updated_at"),
                "owner_login": owner_login,
                "owner_type": owner_type,
                "repository_id": repository_id,
                "repository_name": repository_name,
            }
        )

    logger.info(f"Transformed {len(transformed)} container packages")
    return transformed


@timeit
def load_container_packages(
    neo4j_session: neo4j.Session,
    packages: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    """
    Load GitHub container packages into the graph.
    """
    logger.debug(f"Loading {len(packages)} container packages for {org_url}")
    load(
        neo4j_session,
        GitHubContainerPackageSchema(),
        packages,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def cleanup_container_packages(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove stale GitHub container packages from the graph.
    """
    logger.debug("Running GitHub container packages cleanup")
    GraphJob.from_node_schema(
        GitHubContainerPackageSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_container_packages(
    neo4j_session: neo4j.Session,
    token: str,
    api_url: str,
    organization: str,
    org_url: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync GitHub container packages for an organization.
    """
    logger.info(f"Syncing container packages for organization {org_url}")

    raw_packages = get_container_packages(token, api_url, organization)

    transformed = transform_container_packages(raw_packages, org_url)
    load_container_packages(neo4j_session, transformed, org_url, update_tag)
    cleanup_container_packages(neo4j_session, common_job_parameters)

    logger.info(
        f"Completed syncing {len(transformed)} container packages for {org_url}"
    )
