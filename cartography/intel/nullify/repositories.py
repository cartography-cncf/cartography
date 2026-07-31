import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.nullify.util import paginate
from cartography.models.nullify.repository import NullifyRepositorySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return paginate(api_session, f"{base_url}/admin/repositories", "repositories")


def transform(repositories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Derive source-control match keys so a NullifyRepository can be linked to the
    GitHubRepository / GitLabProject the source-control modules ingest. Nullify exposes
    ``platform``, ``owner`` and ``repository`` (name) but no full URL, so we build:
      - GitHub: ``fullname`` = ``<owner>/<repository>`` (matches GitHubRepository.fullname)
      - GitLab: ``web_url`` = ``https://gitlab.com/<owner>/<repository>``
    The unused key stays None, so the matcher no-ops for the other platform.
    """
    for repo in repositories:
        platform = (repo.get("platform") or "").lower()
        owner = repo.get("owner")
        name = repo.get("repository")
        repo["_github_fullname"] = None
        repo["_gitlab_web_url"] = None
        if owner and name:
            if "github" in platform:
                repo["_github_fullname"] = f"{owner}/{name}"
            elif "gitlab" in platform:
                repo["_gitlab_web_url"] = f"https://gitlab.com/{owner}/{name}"
    return repositories


@timeit
def load_repositories(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NullifyRepositorySchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(NullifyRepositorySchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    repositories = get(api_session, base_url)
    load_repositories(neo4j_session, transform(repositories), tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return repositories
