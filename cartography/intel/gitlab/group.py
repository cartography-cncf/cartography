import logging
import time
from typing import Any
from typing import Dict
from typing import List
from urllib.parse import quote

import neo4j

from cartography.intel.gitlab.pagination import paginate_request
from cartography.util import make_requests_url
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_groups(hosted_domain: str, access_token: str):
    """
    As per the rest api docs: https://docs.gitlab.com/api/api_resources.html
    List Groups: https://docs.gitlab.com/api/groups/#list-all-groups
    Pagination: https://docs.gitlab.com/api/rest/#pagination
    """
    url = f"{hosted_domain}/api/v4/groups?per_page=100"
    groups = paginate_request(url, access_token)

    return groups


@timeit
def get_group(hosted_domain: str, access_token: str, group_id: int) -> Dict:
    """
    Fetch information about a particular group.
    Group Details: https://docs.gitlab.com/api/groups/#details-of-a-group
    """
    url_encoded_group_id = quote(str(group_id), safe="")
    url = f"{hosted_domain}/api/v4/groups/{url_encoded_group_id}"
    response = make_requests_url(url, access_token)

    return response


@timeit
def get_namespace(hosted_domain: str, access_token: str, group_id: int) -> Dict:
    """
    Fetch information about a particular group.
    Group Details: https://docs.gitlab.com/api/namespaces/#get-namespace-by-id
    """
    url_encoded_group_id = quote(str(group_id), safe="")
    url = f"{hosted_domain}/api/v4/namespaces/{url_encoded_group_id}"
    response = make_requests_url(url, access_token)

    return response


def load_group_data(
    session: neo4j.Session,
    group_data: List[Dict],
    common_job_parameters: Dict,
) -> None:
    session.execute_write(_load_group_data, group_data, common_job_parameters)


def _load_group_data(
    tx: neo4j.Transaction,
    group_data: List[Dict],
    common_job_parameters: Dict,
):
    ingest_group_query = """
    UNWIND $groups AS grp
    WITH grp
    WHERE grp.id IS NOT NULL AND grp.name IS NOT NULL
    MERGE (group:GitLabGroup{id: grp.full_path})
    ON CREATE SET
        group.firstseen = timestamp(),
        group.created_at = grp.created_at,
        group.group_id = grp.id

    SET
        group.path = grp.path,
        group.name = grp.name,
        group.description = grp.description,
        group.visibility = grp.visibility,
        group.web_url = grp.web_url,
        group.archived = grp.archived,
        group.full_name = grp.full_name,
        group.avatar_url = grp.avatar_url,
        group.full_path = grp.full_path,
        group.organization_id = grp.organization_id,
        group.parent_id = grp.parent_id,
        group.plan = grp.plan,
        group.trial = grp.trial,
        group.projects_count = grp.projects_count,
        group.lastupdated = $UpdateTag

    WITH group

    MATCH (owner:CloudanixWorkspace{id:$workspace_id})
    MERGE (group)<-[o:OWNER]-(owner)
    ON CREATE SET
        o.firstseen = timestamp()
    SET
        o.lastupdated = $UpdateTag
    """

    tx.run(
        ingest_group_query,
        groups=group_data,
        UpdateTag=common_job_parameters["UPDATE_TAG"],
        workspace_id=common_job_parameters["WORKSPACE_ID"],
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("gitlab_group_cleanup.json", neo4j_session, common_job_parameters)


def sync(
    neo4j_session: neo4j.Session,
    groups: List[Dict],
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
    logger.info("Syncing Groups at %s.", tic)

    load_group_data(neo4j_session, groups, common_job_parameters)

    cleanup(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process Groups '{len(groups)}': {toc - tic:0.4f} seconds")
