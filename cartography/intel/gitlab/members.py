import logging
import time
from typing import Any
from typing import Dict
from typing import List
from urllib.parse import quote

import neo4j

from cartography.intel.gitlab.pagination import paginate_request
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_group_members(hosted_domain: str, access_token: str, group_id: int):
    """
    As per the rest api docs: https://docs.gitlab.com/api/members.html
    Pagination: https://docs.gitlab.com/api/rest/#pagination
    """
    url_encoded_group_id = quote(str(group_id), safe="")
    url = f"{hosted_domain}/api/v4/groups/{url_encoded_group_id}/members?per_page=100"
    members = paginate_request(url, access_token)

    return members


def load_members_data(
    session: neo4j.Session,
    members_data: List[Dict],
    common_job_parameters: Dict,
    group_id: int,
) -> None:
    # Ensure that we only process members that have an ID.
    # Some members, like invited members, may not have an ID.
    valid_members = [member for member in members_data if member.get("id")]
    if not valid_members:
        logger.warning("No valid GitLab members with IDs found to sync.")
        return

    session.execute_write(_load_members_data, valid_members, common_job_parameters, group_id)


def _load_members_data(tx: neo4j.Transaction, members_data: List[Dict], common_job_parameters: Dict, group_id: int):
    ingest_group_query = """
    UNWIND $membersData as member
    MERGE (mem:GitLabMember {id: member.username})
    ON CREATE SET
        mem.firstseen = timestamp(),
        mem.created_at = member.created_at

    SET
        mem.name = member.name,
        mem.username = member.username,
        mem.state = member.state,
        mem.profile_url = member.web_url,
        mem.created_by = member.created_by,
        mem.access_level = member.access_level,
        mem.avatar_url = member.avatar_url,
        mem.email = member.public_email,
        mem.expires_at = member.expires_at,
        mem.group_id = member.group_id,
        mem.locked = member.locked,
        mem.membership_state = member.membership_state,
        mem.web_url = member.web_url,
        mem.lastupdated = $UpdateTag

    WITH mem
    MATCH (owner:GitLabGroup {id: $GroupId})
    MERGE (owner)-[o:MEMBER]->(mem)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = $UpdateTag

    """
    for member in members_data:
        member["created_by"] = member.get("created_by", {}).get("username") if member.get("created_by") else None

    tx.run(
        ingest_group_query,
        membersData=members_data,
        UpdateTag=common_job_parameters["UPDATE_TAG"],
        GroupId=group_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("gitlab_group_member_cleanup.json", neo4j_session, common_job_parameters)


def sync(
    neo4j_session: neo4j.Session,
    group_id: int,
    hosted_domain: str,
    access_token: str,
    common_job_parameters: Dict[str, Any],
    group_name: str,
) -> None:
    """
    Performs the sequential tasks to collect, transform, and sync gitlab data
    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common job parameters containing UPDATE_TAG
    :return: Nothing
    """
    tic = time.perf_counter()

    logger.info("Syncing Members for Gitlab Group '%s', at %s.", group_name, tic)

    group_members = get_group_members(hosted_domain, access_token, group_id)

    load_members_data(neo4j_session, group_members, common_job_parameters, group_id)
    cleanup(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process Members for Gitlab Group '{group_name}': {toc - tic:0.4f} seconds")
