"""
GitHub Packages Intelligence Module.

Syncs container packages (GitHub Container Registry) into the graph.
Only `package_type=container` packages are fetched — other package types
(npm, maven, etc.) are out of scope for this module.
"""

import logging
from typing import Any
from urllib.parse import quote

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.github.util import call_github_rest_api
from cartography.intel.github.util import fetch_all_rest_api_pages
from cartography.intel.github.util import rest_api_base_url
from cartography.models.github.packages import GitHubPackageSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _ghcr_uri(org_login: str, package_name: str) -> str:
    """Build the canonical lowercase GHCR URI for a package."""
    return f"ghcr.io/{org_login.lower()}/{package_name.lower()}"


@timeit
def get_container_packages(
    token: Any,
    api_url: str,
    organization: str,
) -> list[dict[str, Any]]:
    """
    Fetch every container package owned by ``organization`` via the GitHub
    REST API. Returns the raw payloads (one per package).
    """
    base_url = rest_api_base_url(api_url)
    endpoint = (
        f"/orgs/{quote(organization)}/packages?package_type=container&per_page=100"
    )
    try:
        return fetch_all_rest_api_pages(
            token, base_url, endpoint, result_key="packages"
        )
    except requests.exceptions.HTTPError as err:
        # Older GitHub Enterprise versions don't expose this endpoint.
        if err.response is not None and err.response.status_code == 404:
            logger.warning(
                "GitHub Packages endpoint not available for org %s (404). "
                "GHCR sync will be skipped for this organization.",
                organization,
            )
            return []
        raise


@timeit
def get_package_versions(
    token: Any,
    api_url: str,
    organization: str,
    package_name: str,
) -> list[dict[str, Any]]:
    """
    Fetch every version of a single container package. The list endpoint is
    paginated; each version corresponds to a unique manifest digest and may
    carry one or more tags in its metadata.
    """
    base_url = rest_api_base_url(api_url)
    endpoint = (
        f"/orgs/{quote(organization)}/packages/container/"
        f"{quote(package_name, safe='')}/versions?per_page=100"
    )
    try:
        return fetch_all_rest_api_pages(
            token, base_url, endpoint, result_key="versions"
        )
    except requests.exceptions.HTTPError as err:
        if err.response is not None and err.response.status_code == 404:
            logger.debug(
                "Versions endpoint not found for package %s/%s; skipping",
                organization,
                package_name,
            )
            return []
        raise


def transform_packages(
    raw_packages: list[dict[str, Any]],
    organization: str,
) -> list[dict[str, Any]]:
    """Shape the package payload for ingestion."""
    transformed: list[dict[str, Any]] = []
    for pkg in raw_packages:
        name = pkg.get("name")
        if not name:
            continue
        repository = pkg.get("repository") or {}
        repository_url = (
            repository.get("html_url") if isinstance(repository, dict) else None
        )
        transformed.append(
            {
                "name": name,
                "package_type": pkg.get("package_type", "container"),
                "visibility": pkg.get("visibility"),
                "uri": _ghcr_uri(organization, name),
                "html_url": pkg.get("html_url"),
                "repository_url": repository_url,
                "created_at": pkg.get("created_at"),
                "updated_at": pkg.get("updated_at"),
            },
        )
    return transformed


@timeit
def load_packages(
    neo4j_session: neo4j.Session,
    packages: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GitHubPackageSchema(),
        packages,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def cleanup_packages(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(GitHubPackageSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_packages(
    neo4j_session: neo4j.Session,
    token: Any,
    api_url: str,
    organization: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Sync container packages for ``organization``. Returns the transformed
    package list so downstream syncs (versions, tags, attestations) can reuse
    it without re-fetching.
    """
    org_url = f"https://github.com/{organization}"
    raw_packages = get_container_packages(token, api_url, organization)
    packages = transform_packages(raw_packages, organization)
    if packages:
        logger.info(
            "Loading %d GitHub container packages for org %s",
            len(packages),
            organization,
        )
        load_packages(neo4j_session, packages, org_url, update_tag)
    cleanup_params = dict(common_job_parameters)
    cleanup_params["org_url"] = org_url
    cleanup_packages(neo4j_session, cleanup_params)
    return packages


__all__ = [
    "call_github_rest_api",  # re-exported for tests that patch this symbol
    "get_container_packages",
    "get_package_versions",
    "sync_packages",
    "transform_packages",
]
