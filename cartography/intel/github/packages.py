"""
GitHub Packages Intelligence Module.

Syncs container packages (GitHub Container Registry) into the graph.
Only `package_type=container` packages are fetched — other package types
(npm, maven, etc.) are out of scope for this module.
"""

import logging
from dataclasses import dataclass
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


@dataclass(frozen=True)
class ContainerPackagesFetchResult:
    """Result of fetching the org's container packages list.

    ``cleanup_safe`` is False when the endpoint was unavailable (404 on older
    GHES, for instance). Cleanup must be skipped in that case so an outage
    does not purge previously-synced ``GitHubPackage`` nodes.
    """

    packages: list[dict[str, Any]]
    cleanup_safe: bool


def _ghcr_uri(org_login: str, package_name: str) -> str:
    """Build the canonical lowercase GHCR URI for a package."""
    return f"ghcr.io/{org_login.lower()}/{package_name.lower()}"


@timeit
def get_container_packages(
    token: Any,
    api_url: str,
    organization: str,
) -> ContainerPackagesFetchResult:
    """
    Fetch every container package owned by ``organization`` via the GitHub
    REST API. Returns the raw payloads alongside a ``cleanup_safe`` flag.

    The ``/orgs/{org}/packages`` endpoint returns 404 on older GHES versions,
    403 when the token is missing the ``read:packages`` scope (the most
    common misconfiguration in the wild: fine-grained PATs always 403 here),
    and 400 when the account is not actually an organization or has packages
    disabled. All three cases set ``cleanup_safe=False`` so previously-synced
    packages are not purged by a missing-scope or endpoint-outage condition.
    """
    base_url = rest_api_base_url(api_url)
    endpoint = (
        f"/orgs/{quote(organization)}/packages?package_type=container&per_page=100"
    )
    try:
        packages = fetch_all_rest_api_pages(
            token,
            base_url,
            endpoint,
            result_key="packages",
            raise_on_status=(400, 403, 404),
        )
        return ContainerPackagesFetchResult(packages=packages, cleanup_safe=True)
    except requests.exceptions.HTTPError as err:
        status = err.response.status_code if err.response is not None else None
        if status == 404:
            logger.warning(
                "GitHub Packages endpoint not available for org %s (404). "
                "GHCR sync will be skipped and cleanup deferred so previously "
                "synced packages are not purged by an endpoint outage.",
                organization,
            )
            return ContainerPackagesFetchResult(packages=[], cleanup_safe=False)
        if status == 403:
            logger.warning(
                "GitHub Packages endpoint refused for org %s (403). The token "
                "is most likely missing the read:packages scope (fine-grained "
                "PATs cannot access Packages and always 403 here). GHCR sync "
                "will be skipped and cleanup deferred to preserve previously "
                "synced packages.",
                organization,
            )
            return ContainerPackagesFetchResult(packages=[], cleanup_safe=False)
        if status == 400:
            logger.warning(
                "GitHub Packages endpoint rejected request for org %s (400). "
                "The account is most likely not an organization (user accounts "
                "are not supported by /orgs/{org}/packages) or has packages "
                "disabled. GHCR sync will be skipped and cleanup deferred to "
                "preserve previously synced packages.",
                organization,
            )
            return ContainerPackagesFetchResult(packages=[], cleanup_safe=False)
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
    """Shape the package payload for ingestion.

    ``name`` and ``html_url`` are required fields per the REST API contract;
    we let ``KeyError`` surface if GitHub ever returns a malformed payload so
    the failure is loud rather than silently dropping the package.
    """
    transformed: list[dict[str, Any]] = []
    for pkg in raw_packages:
        repository = pkg.get("repository") or {}
        repository_url = (
            repository.get("html_url") if isinstance(repository, dict) else None
        )
        transformed.append(
            {
                "name": pkg["name"],
                "package_type": pkg.get("package_type", "container"),
                "visibility": pkg.get("visibility"),
                "uri": _ghcr_uri(organization, pkg["name"]),
                "html_url": pkg["html_url"],
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
) -> ContainerPackagesFetchResult:
    """
    Sync container packages for ``organization``. Returns the fetch result
    (transformed packages + ``cleanup_safe`` flag) so downstream syncs can
    reuse the data and so the orchestrator can propagate the cleanup_safe
    signal.
    """
    org_url = f"https://github.com/{organization}"
    fetch_result = get_container_packages(token, api_url, organization)
    packages = transform_packages(fetch_result.packages, organization)
    if packages:
        logger.info(
            "Loading %d GitHub container packages for org %s",
            len(packages),
            organization,
        )
        load_packages(neo4j_session, packages, org_url, update_tag)
    if fetch_result.cleanup_safe:
        cleanup_params = dict(common_job_parameters)
        cleanup_params["org_url"] = org_url
        cleanup_packages(neo4j_session, cleanup_params)
    else:
        logger.warning(
            "Skipping GitHubPackage cleanup for org %s because the packages "
            "endpoint discovery was incomplete.",
            organization,
        )
    return ContainerPackagesFetchResult(
        packages=packages,
        cleanup_safe=fetch_result.cleanup_safe,
    )


__all__ = [
    "call_github_rest_api",  # re-exported for tests that patch this symbol
    "get_container_packages",
    "get_package_versions",
    "sync_packages",
    "transform_packages",
]
