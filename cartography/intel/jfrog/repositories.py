import logging
from typing import Any
from urllib.parse import urlparse

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.jfrog.repository import JFrogArtifactoryRepositorySchema
from cartography.models.jfrog.tenant import JFrogArtifactoryTenantSchema
from cartography.util import backoff_handler
from cartography.util import retries_with_backoff
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)


def _call_api(
    api_session: requests.Session,
    method: str,
    url: str,
) -> Any:
    wrapped = retries_with_backoff(
        func=_call_api_base,
        exception_type=requests.exceptions.RequestException,
        max_tries=5,
        on_backoff=backoff_handler,
    )
    return wrapped(api_session, method, url)


def _call_api_base(
    api_session: requests.Session,
    method: str,
    url: str,
) -> Any:
    response = api_session.request(method=method, url=url, timeout=_TIMEOUT)
    response.raise_for_status()
    return response.json()


@timeit
def get_repositories(
    api_session: requests.Session,
    artifactory_base_url: str,
) -> list[dict[str, Any]]:
    list_url = f"{artifactory_base_url.rstrip('/')}/artifactory/api/repositories"
    repositories: list[dict[str, Any]] = _call_api(api_session, "GET", list_url)

    enriched: list[dict[str, Any]] = []
    for repo in repositories:
        key = repo.get("key")
        if not key:
            continue
        details_url = (
            f"{artifactory_base_url.rstrip('/')}/artifactory/api/repositories/{key}"
        )
        try:
            details = _call_api(api_session, "GET", details_url)
        except requests.exceptions.RequestException as e:
            logger.warning("Failed to fetch details for repository %s: %s", key, e)
            details = {}

        enriched.append({**repo, **details})

    return enriched


def transform_repositories(
    repositories: list[dict[str, Any]], tenant_id: str
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for repo in repositories:
        key = repo.get("key")
        if not key:
            continue
        transformed.append(
            {
                "id": f"{tenant_id}:{key}",
                "key": key,
                "description": repo.get("description"),
                "package_type": repo.get("packageType") or repo.get("package_type"),
                "repo_type": repo.get("type") or repo.get("repo_type"),
                "url": repo.get("url"),
                "project_key": repo.get("projectKey"),
                "rclass": repo.get("rclass"),
            }
        )
    return transformed


@timeit
def load_tenant(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    artifactory_base_url: str,
    update_tag: int,
) -> None:
    parsed = urlparse(artifactory_base_url)
    tenant_name = parsed.netloc or tenant_id
    load(
        neo4j_session,
        JFrogArtifactoryTenantSchema(),
        [{"id": tenant_id, "name": tenant_name, "base_url": artifactory_base_url}],
        lastupdated=update_tag,
    )


@timeit
def load_repositories(
    neo4j_session: neo4j.Session,
    repositories: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        JFrogArtifactoryRepositorySchema(),
        repositories,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        JFrogArtifactoryRepositorySchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(JFrogArtifactoryTenantSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    artifactory_base_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    repositories = get_repositories(api_session, artifactory_base_url)
    transformed = transform_repositories(repositories, tenant_id)
    load_tenant(neo4j_session, tenant_id, artifactory_base_url, update_tag)
    load_repositories(neo4j_session, transformed, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
