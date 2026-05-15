import logging
import time
from typing import Any
from typing import Dict
from typing import List

import neo4j
from clouduniqueid.clouds.bitbucket import BitbucketUniqueId

from .common import cleanse_string
from cartography.util import make_requests_url
from cartography.util import timeit

logger = logging.getLogger(__name__)

bitbucket_linker = BitbucketUniqueId()


@timeit
def get_workspaces(access_token: str) -> List[Dict]:
    # https://developer.atlassian.com/cloud/bitbucket/rest/api-group-workspaces/#api-workspaces-get
    url = "https://api.bitbucket.org/2.0/workspaces?pagelen=100"
    response = make_requests_url(url, access_token)
    workspaces = response.get('values', [])

    while 'next' in response:
        response = make_requests_url(response.get('next'), access_token)
        workspaces.extend(response.get('values', []))

    return workspaces


@timeit
def get_workspace(access_token: str, workspace: str) -> Dict:
    # https://developer.atlassian.com/cloud/bitbucket/rest/api-group-workspaces/#api-workspaces-workspace-get
    url =f'https://api.bitbucket.org/2.0/workspaces/{workspace}'
    response = make_requests_url(url, access_token)

    return response


def transform_workspaces(workspaces: List[Dict]) -> List[Dict]:
    for workspace in workspaces:
        workspace['uuid'] = workspace['uuid'].replace('{', '').replace('}', '')

        data = {
            "workspace": cleanse_string(workspace["slug"]),
        }
        workspace['uniqueId'] = bitbucket_linker.get_unique_id(service="bitbucket", data=data, resource_type="workspace")

    return workspaces


def load_workspace_data(session: neo4j.Session, workspace_data: List[Dict], common_job_parameters: Dict) -> None:
    session.execute_write(_load_workspace_data, workspace_data, common_job_parameters)


def _load_workspace_data(tx: neo4j.Transaction, workspace_data: List[Dict], common_job_parameters: Dict) -> None:
    ingest_workspace = """
    MERGE (work:BitbucketWorkspace{id: $uuid})
    ON CREATE SET
        work.firstseen = timestamp(),
        work.created_on = $created_on

    SET
        work.slug = $slug,
        work.type = $type,
        work.name= $name,
        work.unique_id = $unique_id,
        work.is_private = $is_private,
        work.lastupdated = $UpdateTag

    WITH work

    MATCH (owner:CloudanixWorkspace{id:$workspace_id})
    MERGE (work)<-[o:OWNER]-(owner)
    ON CREATE SET
        o.firstseen = timestamp()
    SET
        o.lastupdated = $UpdateTag

    """
    for workspace in workspace_data:
        tx.run(
            ingest_workspace,

            name=workspace.get("name"),
            unique_id=workspace.get("uniqueId"),
            created_on=workspace.get('created_on'),
            slug=workspace.get('slug'),
            type=workspace.get('type'),
            uuid=workspace.get('uuid'),
            is_private=workspace.get('is_private'),
            UpdateTag=common_job_parameters['UPDATE_TAG'],
            workspace_id=common_job_parameters['WORKSPACE_ID'],
        )


def sync(
        neo4j_session: neo4j.Session,
        workspaces: List[Dict],
        common_job_parameters: Dict[str, Any],

) -> None:
    """
    Performs the sequential tasks to collect, transform, and sync bitbucket data
    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common job parameters containing UPDATE_TAG
    :return: Nothing
    """
    tic = time.perf_counter()
    logger.info("BEGIN Syncing Bitbucket Workspaces", extra={"workspace": common_job_parameters["WORKSPACE_ID"], "start": tic})

    workspaces = transform_workspaces(workspaces)
    load_workspace_data(neo4j_session, workspaces, common_job_parameters)

    toc = time.perf_counter()
    logger.info("END Syncing Bitbucket Workspaces", extra={"workspace": common_job_parameters["WORKSPACE_ID"], "end": toc, "duration": f"{toc - tic:0.4f}"})
