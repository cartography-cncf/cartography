import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j

from cartography.intel.gitlab.pagination import paginate_request
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_dependencies(hosted_domain: str, access_token: str, project: str):
    """
    As per the rest api docs: https://docs.gitlab.com/api/dependencies.html#list-project-dependencies
    Pagination: https://docs.gitlab.com/api/rest/#pagination
    """
    url = f"{hosted_domain}/api/v4/projects/{project}/dependencies?per_page=100"
    dependencies = paginate_request(url, access_token)

    return dependencies


def load_dependencies_data(
    session: neo4j.Session,
    dependencies_data: List[Dict],
    project_id: str,
    common_job_parameters: Dict,
) -> None:
    session.execute_write(_load_dependencies_data, dependencies_data, project_id, common_job_parameters)


def _load_dependencies_data(
    tx: neo4j.Transaction,
    dependencies_data: List[Dict],
    project_id: str,
    common_job_parameters: Dict,
):
    ingest_dependencies = """
    UNWIND $dependenciesData AS dependency
    MERGE (dep:GitLabDependency {id: dependency.name})
    ON CREATE SET dep.firstseen = timestamp()
    dep.created_at = dependency.created_at

    SET dep.name = dependency.name,
    dep.id = dependency.id,
    dep.version = dependency.version,
    dep.dependency_file_path = dependency.dependency_file_path,
    dep.vulnerabilities = dependency.vulnerabilities,
    dep.licenses = dependency.licenses,
    dep.lastupdated = $UpdateTag

    WITH dep, dependency
    MATCH (repo:GitLabProject {id: $ProjectID})
    MERGE (dep)-[r:HAS]->(repo)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """

    tx.run(
        ingest_dependencies,
        dependenciesData=dependencies_data,
        ProjectID=project_id,
        UpdateTag=common_job_parameters["UPDATE_TAG"],
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("gitlab_project_dependencies_cleanup.json", neo4j_session, common_job_parameters)


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
    logger.info("Syncing Gitlab All Dependencies")
    project_dependencies = get_dependencies(hosted_domain, access_token, project_id)
    load_dependencies_data(neo4j_session, project_dependencies, project_id, common_job_parameters)
    cleanup(neo4j_session, common_job_parameters)
