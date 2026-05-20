import logging
import time
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from typing import Dict
from typing import List
from urllib.parse import quote

import neo4j

from cartography.intel.gitlab.pagination import paginate_request
from cartography.util import make_requests_url
from cartography.util import normalize_datetime
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_group_projects(hosted_domain: str, access_token: str, group_id: int):
    """
    As per the rest api docs: https://docs.gitlab.com/api/groups/#list-projects
    Pagination: https://docs.gitlab.com/api/rest/#pagination
    """
    url_encoded_group_id = quote(str(group_id), safe="")
    url = f"{hosted_domain}/api/v4/groups/{url_encoded_group_id}/projects?include_subgroups=true&per_page=100"
    projects = paginate_request(url, access_token)

    return projects


@timeit
def get_project_languages(hosted_domain: str, access_token: str, project_id: int):
    """
    As per the rest api docs: https://docs.gitlab.com/api/projects/#list-programming-languages-used
    Pagination: https://docs.gitlab.com/api/rest/#pagination
    """
    url = f"{hosted_domain}/api/v4/projects/{project_id}/languages"
    languages = make_requests_url(url, access_token)

    return languages


@timeit
def get_project_branches(hosted_domain: str, access_token: str, project_id: int):
    """
    As per the rest api docs: https://docs.gitlab.com/api/branches/#list-repository-branches
    Pagination: https://docs.gitlab.com/api/rest/#pagination
    """
    url = f"{hosted_domain}/api/v4/projects/{project_id}/repository/branches?per_page=100"
    branches = paginate_request(url, access_token)

    return branches


def transform_projects_data(projects: List[Dict]) -> List[Dict]:
    for project in projects:
        project["is_private"] = project["visibility"] == "private"
        project["archived"] = project.get("archived", False)
        iso_str, ts_ms = normalize_datetime(project.get("last_activity_at"))
        project["last_activity_at"] = iso_str
        project["last_activity_at_timestamp"] = ts_ms

    return projects


def transform_branches_data(branches: List[Dict], project_id: int, project_path: str, default_branch: str = None) -> List[Dict]:
    """
    Transform branch data and filter to include only:
    - Branches active in the last 180 days
    - Default branch (always included)
    """
    transformed_branches = []
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=180)

    for branch in branches:
        branch_name = branch["name"]
        commit = branch.get("commit", {})
        committed_date_str = commit.get("committed_date")

        # Always include default branch
        if branch_name == default_branch:
            transformed_branches.append({
                "project_id": project_id,
                "project_path": project_path,
                "id": f"{project_id}:{branch_name}",
                "name": branch_name,
                "committed_date": committed_date_str,
            })
            continue

        # Filter by activity date
        if committed_date_str:
            committed_date = datetime.fromisoformat(committed_date_str.replace('Z', '+00:00'))
            if committed_date >= cutoff_date:
                transformed_branches.append({
                    "project_id": project_id,
                    "project_path": project_path,
                    "id": f"{project_id}:{branch_name}",
                    "name": branch_name,
                    "committed_date": committed_date_str,
                })
        else:
            transformed_branches.append({
                "project_id": project_id,
                "project_path": project_path,
                "id": f"{project_id}:{branch_name}",
                "name": branch_name,
                "committed_date": committed_date_str,
            })

    return transformed_branches


def load_projects_data(
    session: neo4j.Session,
    project_data: List[Dict],
    common_job_parameters: Dict,
    group_id: int,
) -> None:
    session.execute_write(
        _load_projects_data,
        project_data,
        common_job_parameters,
        group_id,
    )


def load_branches_data(
    session: neo4j.Session,
    branches_data: List[Dict],
    common_job_parameters: Dict,
) -> None:
    session.execute_write(
        _load_branches_data,
        branches_data,
        common_job_parameters,
    )


def _load_branches_data(
    tx: neo4j.Transaction,
    branches_data: List[Dict],
    common_job_parameters: Dict,
) -> None:
    ingest_branches = """
    UNWIND $branchesData as branch
    MERGE (br:GitLabBranch{id:branch.id})
    ON CREATE SET br.firstseen = timestamp()
    SET br.name = branch.name,
    br.committed_date = branch.committed_date,
    br.projectid = branch.project_id,
    br.lastupdated = $UpdateTag

    WITH br, branch
    MATCH (project:GitLabProject{path_with_namespace:branch.project_path})
    MERGE (project)-[r:BRANCH]->(br)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """

    tx.run(
        ingest_branches,
        branchesData=branches_data,
        UpdateTag=common_job_parameters["UPDATE_TAG"],
    )


def _load_projects_data(
    tx: neo4j.Transaction,
    project_data: List[Dict],
    common_job_parameters: Dict,
    group_id: int,
) -> None:
    ingest_group = """
    UNWIND $projectData as project
    MERGE (pro:GitLabProject {id: project.path})
    ON CREATE SET
        pro.firstseen = timestamp(),
        pro.created_at = project.created_at

    SET
        pro.name = project.name,
        pro.archived = project.archived,
        pro.avatar_url = project.avatar_url,
        pro.creator_id = project.creator_id,
        pro.web_url = project.web_url,
        pro.path = project.path,
        pro.id = project.id,
        pro.projectid = project.id,
        pro.path_with_namespace = project.path_with_namespace,
        pro.description = project.description,
        pro.name_with_namespace = project.name_with_namespace,
        pro.visibility = project.visibility,
        pro.is_private = project.is_private,
        pro.namespace= project.namespace.path,
        pro.last_activity_at = project.last_activity_at,
        pro.last_activity_at_timestamp = project.last_activity_at_timestamp,
        pro.default_branch = project.default_branch,
        pro.primary_language = project.primary_language,
        pro.lastupdated = $UpdateTag

    WITH pro, project
    MATCH (group:GitLabGroup{id: $GroupId})
    MERGE (group)-[r:RESOURCE]->(pro)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """

    tx.run(
        ingest_group,
        projectData=project_data,
        UpdateTag=common_job_parameters["UPDATE_TAG"],
        GroupId=group_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        "gitlab_group_project_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


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

    logger.info("Syncing Projects for Gitlab Group '%s', at %s.", group_name, tic)

    group_projects = get_group_projects(hosted_domain, access_token, group_id)

    for project in group_projects:
        project_languages = get_project_languages(
            hosted_domain,
            access_token,
            project["id"],
        )
        if project_languages:
            primary_language = max(project_languages, key=project_languages.get)
            project["primary_language"] = primary_language.lower()

    group_projects = transform_projects_data(group_projects)

    load_projects_data(neo4j_session, group_projects, common_job_parameters, group_id)

    # Sync branches for each project
    for project in group_projects:
        branches = get_project_branches(hosted_domain, access_token, project["id"])
        transformed_branches = transform_branches_data(
            branches,
            project["id"],
            project.get("path_with_namespace", project["path"]),
            project.get("default_branch"),
        )
        load_branches_data(neo4j_session, transformed_branches, common_job_parameters)

    cleanup(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(
        f"Time to process Projects for Gitlab Group '{group_name}': {toc - tic:0.4f} seconds",
    )
