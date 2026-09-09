import logging
from typing import Any

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.socketdev.repository import SocketDevRepositorySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)
_BASE_URL = "https://api.socket.dev/v0"
_PAGE_SIZE = 100
_RETRY_POLICY = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)


@timeit
def get(api_token: str, org_slug: str) -> list[dict[str, Any]]:
    """
    Fetch all repositories for the given Socket.dev organization.
    Handles pagination automatically.
    """
    all_repos: list[dict[str, Any]] = []
    page = 1
    api_session = requests.Session()
    api_session.mount("https://", HTTPAdapter(max_retries=_RETRY_POLICY))
    api_session.headers.update(
        {
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json",
        },
    )

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
        for repo in results:
            # Some Socket deployments omit this key from list responses. An explicit
            # null means the repository has no GitHub integration.
            if "integration_meta" not in repo and repo.get("slug"):
                detail_response = api_session.get(
                    f"{_BASE_URL}/orgs/{org_slug}/repos/{repo['slug']}",
                    params=(
                        {"workspace": repo["workspace"]}
                        if "workspace" in repo
                        else None
                    ),
                    timeout=_TIMEOUT,
                )
                detail_response.raise_for_status()
                repo = {**repo, **detail_response.json()}
            all_repos.append(repo)

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
    raw_repos = get(api_token, org_slug)
    repositories = transform(raw_repos)
    org_id = common_job_parameters["ORG_ID"]
    load_repositories(neo4j_session, repositories, org_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed Socket.dev repositories sync")
