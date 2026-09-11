import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.socketdev.util import _create_session
from cartography.models.socketdev.repository import SocketDevRepositorySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)
_BASE_URL = "https://api.socket.dev/v0"
_PAGE_SIZE = 100
_MAX_ENRICHMENT_WORKERS = 8


def _fetch_integration_meta(
    api_session: requests.Session,
    org_slug: str,
    repo: dict[str, Any],
) -> tuple[bool, dict[str, Any] | None]:
    response = api_session.get(
        f"{_BASE_URL}/orgs/{org_slug}/repos/{repo['slug']}",
        params={"workspace": repo["workspace"]} if repo.get("workspace") else None,
        timeout=_TIMEOUT,
    )
    if 400 <= response.status_code < 500:
        logger.warning(
            "Skipping Socket.dev repository identity enrichment for org '%s', "
            "repository '%s' after HTTP %d",
            org_slug,
            repo["slug"],
            response.status_code,
        )
        return False, None
    response.raise_for_status()
    return True, response.json().get("integration_meta")


def _enrich_missing_integration_meta(
    api_token: str,
    org_slug: str,
    repositories: list[dict[str, Any]],
) -> set[str]:
    # Socket list responses may omit this field. Keep explicit null as the
    # provider-reported absence of an integration.
    candidates = [
        repo
        for repo in repositories
        if "integration_meta" not in repo and repo.get("slug")
    ]
    if not candidates:
        return set()

    worker_count = min(_MAX_ENRICHMENT_WORKERS, len(candidates))
    logger.info(
        "Enriching GitHub identity for %d Socket.dev repositories with %d workers",
        len(candidates),
        worker_count,
    )

    batches = [candidates[index::worker_count] for index in range(worker_count)]

    def enrich_batch(batch: list[dict[str, Any]]) -> set[str]:
        incomplete_repository_ids = set()
        with _create_session(api_token) as api_session:
            for repo in batch:
                fetched, integration_meta = _fetch_integration_meta(
                    api_session,
                    org_slug,
                    repo,
                )
                if fetched:
                    repo["integration_meta"] = integration_meta
                else:
                    incomplete_repository_ids.add(repo["id"])
        return incomplete_repository_ids

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        incomplete_batches = list(executor.map(enrich_batch, batches))
    return set().union(*incomplete_batches)


@timeit
def get(api_token: str, org_slug: str) -> tuple[list[dict[str, Any]], set[str]]:
    """
    Fetch all repositories for the given Socket.dev organization.
    Handles pagination automatically.

    Returns the repositories and the IDs whose identity enrichment was incomplete.
    """
    all_repos: list[dict[str, Any]] = []
    page = 1
    with _create_session(api_token) as api_session:
        while True:
            response = api_session.get(
                f"{_BASE_URL}/orgs/{org_slug}/repos",
                params={
                    "per_page": _PAGE_SIZE,
                    "page": page,
                },
                timeout=_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            all_repos.extend(results)

            next_page = data.get("nextPage")
            if not next_page or not results:
                break
            page = next_page

    incomplete_repository_ids = _enrich_missing_integration_meta(
        api_token,
        org_slug,
        all_repos,
    )

    logger.debug("Fetched %d Socket.dev repositories", len(all_repos))
    return all_repos, incomplete_repository_ids


def transform(raw_repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Transform raw repository data for ingestion.
    """
    repos = []
    for repo in raw_repos:
        # default_branch can be a dict {"name": "main", "type": ...} or a string
        default_branch = repo.get("default_branch")
        if isinstance(default_branch, dict):
            default_branch = default_branch.get("name")

        # Keep Socket's repository identity for alert and dependency relationships.
        workspace = repo.get("workspace")
        slug = repo.get("slug")
        fullname = f"{workspace}/{slug}" if workspace and slug else slug

        integration_meta = repo.get("integration_meta") or {}
        integration_value = integration_meta.get("value") or {}
        github_owner = integration_value.get("installation_login")
        github_repo = integration_value.get("repo_name")
        repository_url = (
            f"https://github.com/{github_owner}/{github_repo}"
            if integration_meta.get("type") == "github" and github_owner and github_repo
            else None
        )

        repos.append(
            {
                "id": repo["id"],
                "name": repo.get("name"),
                "slug": slug,
                "fullname": fullname,
                "repository_url": repository_url,
                "description": repo.get("description"),
                "visibility": repo.get("visibility"),
                "archived": repo.get("archived"),
                "default_branch": default_branch,
                "homepage": repo.get("homepage"),
                "created_at": repo.get("created_at"),
                "updated_at": repo.get("updated_at"),
            },
        )
    return repos


@timeit
def load_repositories(
    neo4j_session: neo4j.Session,
    repositories: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SocketDevRepositorySchema(),
        repositories,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        SocketDevRepositorySchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_repositories(
    neo4j_session: neo4j.Session,
    api_token: str,
    org_slug: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Socket.dev repositories for the given organization.
    """
    logger.info("Starting Socket.dev repositories sync")
    raw_repos, incomplete_repository_ids = get(api_token, org_slug)
    repositories = transform(
        [repo for repo in raw_repos if repo["id"] not in incomplete_repository_ids],
    )
    org_id = common_job_parameters["ORG_ID"]
    load_repositories(neo4j_session, repositories, org_id, update_tag)
    if not incomplete_repository_ids:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping Socket.dev repository cleanup for org '%s' because "
            "repository identity enrichment was incomplete",
            org_slug,
        )
    logger.info("Completed Socket.dev repositories sync")
