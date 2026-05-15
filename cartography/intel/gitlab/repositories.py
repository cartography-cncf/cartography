import logging
import time
from typing import Any
from typing import Dict
from typing import List

import neo4j

from cartography.intel.gitlab.pagination import paginate_request
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_repos(hosted_domain: str, access_token: str, project: str):
    """
    As per the rest api docs: https://docs.gitlab.com/api/repositories.html#list-repository-tree
    Pagination: https://docs.gitlab.com/api/rest/#pagination
    """
    url = f"{hosted_domain}/api/v4/projects/{project}/repository/tree?per_page=100"
    repositories = paginate_request(url, access_token)

    return repositories


def load_repositories_data(
    session: neo4j.Session,
    repos_data: List[Dict],
    project_id: str,
    common_job_parameters: Dict,
) -> None:
    session.execute_write(_load_repositories_data, repos_data, project_id, common_job_parameters)


def _load_repositories_data(
    tx: neo4j.Transaction,
    repos_data: List[Dict],
    project_id: str,
    common_job_parameters: Dict,
):
    ingest_repositories = """
    UNWIND $reposData as repo
    MERGE (re:GitLabRepository{id: repo.path})
    ON CREATE SET re.firstseen = timestamp(),
    re.created_at = repo.created_at

    SET re.name = repo.name,
    re.id = repo.id,
    re.type = repo.type,
    re.path = repo.path,
    re.mode = repo.mode,
    re.lastupdated = $UpdateTag

    WITH re, repo
    MATCH (project:GitLabProject{id: $ProjectID})
    MERGE (project)<-[o:HAS]-(re)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = $UpdateTag
    """

    tx.run(
        ingest_repositories,
        reposData=repos_data,
        ProjectID=project_id,
        UpdateTag=common_job_parameters["UPDATE_TAG"],
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("gitlab_project_repositories_cleanup.json", neo4j_session, common_job_parameters)


def sync(
    neo4j_session: neo4j.Session,
    project_id: str,
    hosted_domain: str,
    access_token: str,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Performs the sequential tasks to collect, transform, and sync gitlab data
    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common job parameters containing UPDATE_TAG
    :return: Nothing
    """
    tic = time.perf_counter()

    logger.info("Syncing Repositories for Gitlab Project '%s', at %s.", project_id, tic)

    project_repos = get_repos(hosted_domain, access_token, project_id)
    load_repositories_data(neo4j_session, project_repos, project_id, common_job_parameters)
    cleanup(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process Repositories for Gitlab Project '{project_id}': {toc - tic:0.4f} seconds")
