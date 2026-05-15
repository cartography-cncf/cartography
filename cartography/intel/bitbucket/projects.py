import logging
import time
from typing import Any
from typing import Dict
from typing import List

import neo4j
from clouduniqueid.clouds.bitbucket import BitbucketUniqueId

from .common import cleanse_string
from cartography.util import make_requests_url
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
bitbucket_linker = BitbucketUniqueId()


@timeit
def get_projects(access_token: str, workspace: str) -> List[Dict]:
    url = f"https://api.bitbucket.org/2.0/workspaces/{workspace}/projects?pagelen=100"

    response = make_requests_url(url, access_token)
    projects = response.get('values', [])

    while 'next' in response:
        response = make_requests_url(response.get('next'), access_token)
        projects.extend(response.get('values', []))

    return projects


def transform_projects(workspace_projects: List[Dict], workspace: str) -> List[Dict]:
    for project in workspace_projects:
        project['workspace']['uuid'] = project['workspace']['uuid'].replace('{', '').replace('}', '')
        project['uuid'] = project['uuid'].replace('{', '').replace('}', '')
        project['slug'] = project['key']

        data = {
            "workspace": workspace,
            "project": cleanse_string(project["slug"]),
        }
        project['uniqueId'] = bitbucket_linker.get_unique_id(service="bitbucket", data=data, resource_type="project")

    return workspace_projects


def load_projects_data(session: neo4j.Session, project_data: List[Dict], common_job_parameters: Dict) -> None:
    session.execute_write(_load_projects_data, project_data, common_job_parameters)


def _load_projects_data(tx: neo4j.Transaction, project_data: List[Dict], common_job_parameters: Dict) -> None:
    ingest_workspace = """
    UNWIND $projectData as project
    MERGE (pro:BitbucketProject{id: project.uuid})
    ON CREATE SET pro.firstseen = timestamp(),
    pro.created_on = project.created_on

    SET pro.description = project.description,
    pro.type = project.type,
    pro.name=project.name,
    pro.unique_id = project.uniqueId,
    pro.is_private = project.is_private,
    pro.has_publicly_visible_repos=project.has_publicly_visible_repos,
    pro.key=project.key,
    pro.slug=project.slug,
    pro.owner=project.owner.display_name,
    pro.type=project.type,
    pro.updated_on=project.updated_on,
    pro.lastupdated = $UpdateTag

    WITH pro,project
    MATCH (work:BitbucketWorkspace{id:project.workspace.uuid})
    merge (work)-[o:RESOURCE]->(pro)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = $UpdateTag
    """

    tx.run(
        ingest_workspace,
        projectData=project_data,
        UpdateTag=common_job_parameters['UPDATE_TAG'],
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('bitbucket_workspace_project_cleanup.json', neo4j_session, common_job_parameters)


def sync(
        neo4j_session: neo4j.Session,
        workspace_name: str,
        bitbucket_access_token: str,
        common_job_parameters: Dict[str, Any],
) -> None:
    """
    Performs the sequential tasks to collect, transform, and sync bitbucket data
    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common job parameters containing UPDATE_TAG
    :return: Nothing
    """
    tic = time.perf_counter()
    logger.info("BEGIN Syncing Bitbucket Projects", extra={"workspace": common_job_parameters["WORKSPACE_ID"], "slug": workspace_name, "start": tic})

    workspace_projects = get_projects(bitbucket_access_token, workspace_name)
    workspace_projects = transform_projects(workspace_projects, workspace_name)
    load_projects_data(neo4j_session, workspace_projects, common_job_parameters)
    cleanup(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info("END Syncing Bitbucket Projects", extra={"workspace": common_job_parameters["WORKSPACE_ID"], "slug": workspace_name, "end": toc, "duration": f"{toc - tic:0.4f}"})
