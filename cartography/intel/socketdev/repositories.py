import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.socketdev.repository import SocketDevRepositorySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)
_BASE_URL = "https://api.socket.dev/v0"
_PAGE_SIZE = 100


@timeit
def get(api_token: str, org_slug: str) -> list[dict[str, Any]]:
    """
    Fetch all repositories for the given Socket.dev organization.
    Handles pagination automatically.
    """
    all_repos: list[dict[str, Any]] = []
    page = 1

    while True:
        response = requests.get(
            f"{_BASE_URL}/orgs/{org_slug}/repos",
            headers={
                "Authorization": f"Bearer {api_token}",
                "Accept": "application/json",
            },
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

    logger.debug("Fetched %d Socket.dev repositories", len(all_repos))
    return all_repos


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

        # Build fullname from workspace/slug for ontology matching
        workspace = repo.get("workspace")
        slug = repo.get("slug")
        fullname = f"{workspace}/{slug}" if workspace and slug else slug

        repos.append(
            {
                "id": repo["id"],
                "name": repo.get("name"),
                "slug": slug,
                "fullname": fullname,
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
    raw_repos = get(api_token, org_slug)
    repositories = transform(raw_repos)
    org_id = common_job_parameters["ORG_ID"]
    load_repositories(neo4j_session, repositories, org_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed Socket.dev repositories sync")
