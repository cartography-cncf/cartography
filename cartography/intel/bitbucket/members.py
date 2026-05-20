import logging
import time
from typing import Any
from typing import Dict
from typing import List

import neo4j
import requests
from clouduniqueid.clouds.bitbucket import BitbucketUniqueId
from requests.exceptions import RequestException

from .common import cleanse_string
from cartography.util import make_requests_url
from cartography.util import run_cleanup_job
from cartography.util import timeit
logger = logging.getLogger(__name__)
bitbucket_linker = BitbucketUniqueId()


@timeit
def get_workspace_members(access_token: str, workspace: str) -> List[Dict]:
    url = f"https://api.bitbucket.org/2.0/workspaces/{workspace}/members?pagelen=100"

    response = make_requests_url(url, access_token)
    members = response.get('values', [])

    while 'next' in response:
        response = make_requests_url(response.get('next'), access_token)
        members.extend(response.get('values', []))

    return members


def transform_members(workspace_members: List[Dict], workspace: str) -> List[Dict]:
    for member in workspace_members:
        member['workspace']['uuid'] = member['workspace']['uuid'].replace('{', '').replace('}', '')
        member['user']['uuid'] = member['user']['uuid'].replace('{', '').replace('}', '')

        data = {
            "workspace": workspace,
            "member": cleanse_string(member["user"]["nickname"]),
        }
        member['uniqueId'] = bitbucket_linker.get_unique_id(service="bitbucket", data=data, resource_type="member")

    return workspace_members


def load_members_data(session: neo4j.Session, members_data: List[Dict], common_job_parameters: Dict) -> None:
    session.execute_write(_load_members_data, members_data, common_job_parameters)


def _load_members_data(tx: neo4j.Transaction, members_data: List[Dict], common_job_parameters: Dict) -> None:
    ingest_workspace = """
    UNWIND $membersData as member
    MERGE (mem:BitbucketMember{id: member.user.uuid})
    ON CREATE SET mem.firstseen = timestamp()

    SET mem.slug = member.slug,
    mem.type = member.user.type,
    mem.name= member.user.display_name,
    mem.account_id=member.user.account_id,
    mem.unique_id = member.uniqueId,
    mem.lastupdated = $UpdateTag

    WITH mem,member
    MATCH (owner:BitbucketWorkspace{id:member.workspace.uuid})
    merge (owner)-[o:MEMBER]->(mem)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = $UpdateTag

    """
    tx.run(
        ingest_workspace,
        membersData=members_data,
        UpdateTag=common_job_parameters['UPDATE_TAG'],
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('bitbucket_workspace_member_cleanup.json', neo4j_session, common_job_parameters)


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
    logger.info("BEGIN Syncing Bitbucket Members", extra={"workspace": common_job_parameters["WORKSPACE_ID"], "slug": workspace_name, "start": tic})

    workspace_members = get_workspace_members(bitbucket_access_token, workspace_name)
    workspace_members = transform_members(workspace_members, workspace_name)
    load_members_data(neo4j_session, workspace_members, common_job_parameters)
    cleanup(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info("END Syncing Bitbucket Members", extra={"workspace": common_job_parameters["WORKSPACE_ID"], "slug": workspace_name, "end": toc, "duration": f"{toc - tic:0.4f}"})
