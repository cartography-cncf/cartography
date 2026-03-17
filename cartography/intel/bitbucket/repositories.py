import logging
import time
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from typing import Dict
from typing import List

import neo4j
from clouduniqueid.clouds.bitbucket import BitbucketUniqueId

from .common import cleanse_string
from cartography.util import make_requests_url
from cartography.util import normalize_datetime
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

bitbucket_linker = BitbucketUniqueId()


@timeit
def get_repos(access_token: str, workspace: str) -> List[Dict]:
    # https://developer.atlassian.com/cloud/bitbucket/rest/api-group-repositories/#api-repositories-workspace-get
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}?pagelen=100"

    response = make_requests_url(url, access_token)
    repositories = response.get("values", [])

    while "next" in response:
        response = make_requests_url(response.get("next"), access_token)
        repositories.extend(response.get("values", []))

    return repositories


@timeit
def get_branches(access_token: str, workspace: str, repo_slug: str) -> List[Dict]:
    # https://developer.atlassian.com/cloud/bitbucket/rest/api-group-repositories/#api-repositories-repository-refs-branches-get
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/refs/branches?pagelen=100"

    response = make_requests_url(url, access_token)
    branches = response.get("values", [])

    while "next" in response:
        response = make_requests_url(response.get("next"), access_token)
        branches.extend(response.get("values", []))

    return branches


def transform_repos(workspace_repos: List[Dict], workspace: str) -> Dict:
    """
    Transform the repos data including languages
    """
    transformed_repo_list = []
    transformed_repo_languages: List[Dict[str, str]] = []

    for repo in workspace_repos:
        # Existing transformations
        repo["workspace"]["uuid"] = repo["workspace"]["uuid"].replace("{", "").replace("}", "")
        repo["project"]["uuid"] = repo["project"]["uuid"].replace("{", "").replace("}", "")
        repo["uuid"] = repo["uuid"].replace("{", "").replace("}", "")
        repo["primary_language"] = repo.get("language", "").lower()
        repo["console_link"] = repo.get("links", {}).get("html", {}).get("href", None)

        if repo is not None and repo.get("mainbranch") is not None:
            repo["default_branch"] = repo.get("mainbranch", {}).get("name", None)

        if repo.get("language"):
            transformed_repo_languages.append(
                {
                    "repo_id": repo["uuid"],
                    "primary_language": repo["primary_language"],
                },
            )

        repo["archived"] = repo.get("is_archived", repo.get("archived", False))
        repo["visibility"] = "private" if repo.get("is_private") else "public"
        data = {
            "workspace": workspace,
            "project": cleanse_string(repo["project"]["name"]),
            "repository": cleanse_string(repo["name"]),
        }

        repo["uniqueId"] = bitbucket_linker.get_unique_id(service="bitbucket", data=data, resource_type="repository")
        transformed_repo_list.append(repo)

    return {
        "repos": transformed_repo_list,
        "repo_primary_language": transformed_repo_languages,
    }


def transform_branches(branches: List[Dict], repo_id: str, default_branch: str = None) -> List[Dict]:
    """
    Transform branch data and filter to include only:
    - Branches active in the last 90 days
    - Default branch (always included)
    """
    transformed_branches = []
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)

    for branch in branches:
        branch_name = branch["name"]
        target = branch.get("target", {})
        date_str = target.get("date")

        # Always include default branch
        if branch_name == default_branch:
            transformed_branches.append({
                "repo_id": repo_id,
                "id": f"{repo_id}:{branch_name}",
                "name": branch_name,
                "date": date_str,
            })
            continue

        # Filter by activity date
        if date_str:
            branch_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            if branch_date >= cutoff_date:
                transformed_branches.append({
                    "repo_id": repo_id,
                    "id": f"{repo_id}:{branch_name}",
                    "name": branch_name,
                    "date": date_str,
                })
        else:
            # No date available, include the branch
            transformed_branches.append({
                "repo_id": repo_id,
                "id": f"{repo_id}:{branch_name}",
                "name": branch_name,
                "date": date_str,
            })

    return transformed_branches


def load_repositories_data(session: neo4j.Session, repos_data: List[Dict], common_job_parameters: Dict) -> None:
    session.write_transaction(_load_repositories_data, repos_data, common_job_parameters)


@timeit
def load_branches(session: neo4j.Session, branches_data: List[Dict], common_job_parameters: Dict) -> None:
    session.write_transaction(_load_branches, branches_data, common_job_parameters)


@timeit
def _load_branches(tx: neo4j.Transaction, branches_data: List[Dict], common_job_parameters: Dict) -> None:
    ingest_branches = """
    UNWIND $branchesData as branch
    MERGE (br:BitbucketBranch{id:branch.id})
    ON CREATE SET br.firstseen = timestamp()
    SET br.name = branch.name,
    br.date = branch.date,
    br.lastupdated = $UpdateTag

    WITH br, branch
    MATCH (repo:BitbucketRepository{id:branch.repo_id})
    MERGE (repo)-[r:BRANCH]->(br)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """

    tx.run(
        ingest_branches,
        branchesData=branches_data,
        UpdateTag=common_job_parameters["UPDATE_TAG"],
    )


@timeit
def load_languages(neo4j_session: neo4j.Session, update_tag: int, repo_primary_language: List[Dict]) -> None:
    """
    Ingest the relationships for repo languages
    :param neo4j_session: Neo4J session object for server communication
    :param update_tag: Timestamp used to determine data freshness
    :param repo_primary_language: list of primary language to repo mappings
    """
    ingest_languages = """
        UNWIND $Languages as lang

        MERGE (pl:ProgrammingLanguage{id: lang.primary_language})
        ON CREATE SET pl.firstseen = timestamp(),
        pl.name = lang.primary_language
        SET pl.lastupdated = $UpdateTag
        WITH pl, lang

        MATCH (repo:BitbucketRepository{id: lang.repo_id})
        MERGE (repo)-[r:PRIMARY_LANGUAGE]->(pl)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $UpdateTag
    """

    neo4j_session.run(
        ingest_languages,
        Languages=repo_primary_language,
        UpdateTag=update_tag,
    )


def _load_repositories_data(tx: neo4j.Transaction, repos_data: List[Dict], common_job_parameters: Dict) -> None:
    ingest_repositories = """
    UNWIND $reposData as repo
    MERGE (re:BitbucketRepository{id:repo.uuid})
    ON CREATE SET re.firstseen = timestamp(),
    re.created_on = repo.created_on

    SET re.slug = repo.slug,
    re.type = repo.type,
    re.unique_id = repo.uniqueId,
    re.name = repo.name,
    re.is_private = repo.is_private,
    re.description = repo.description,
    re.full_name = repo.full_name,
    re.has_issues = repo.has_issues,
    re.primary_language = repo.primary_language,
    re.owner = repo.owner.display_name,
    re.parent = repo.parent.name,
    re.default_branch = repo.default_branch,
    re.archived = repo.archived,
    re.updated_on = repo.updated_on,
    re.visibility = repo.visibility,
    re.lastupdated = $UpdateTag,
    re.console_link = repo.console_link

    WITH re, repo
    MATCH (project:BitbucketProject{id:repo.project.uuid})
    MERGE (project)<-[o:RESOURCE]-(re)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = $UpdateTag
    """

    tx.run(
        ingest_repositories,
        reposData=repos_data,
        UpdateTag=common_job_parameters["UPDATE_TAG"],
    )


def _update_repo_last_activity(
    neo4j_session: neo4j.Session,
    repo_id: str,
    branches: List[Dict],
    default_branch: str,
) -> None:
    """
    Compute and store last_activity_at for a Bitbucket repository from its branch commit dates.
    Priority: (1) default branch commit date, (2) max commit date across all branches.
    """
    last_activity_at = None
    # Priority 1: default branch commit date
    if default_branch:
        for b in branches:
            if b["name"] == default_branch and b.get("date"):
                last_activity_at = b["date"]
                break

    # Priority 2: max across all branches
    if last_activity_at is None:
        all_dates = [b["date"] for b in branches if b.get("date")]
        last_activity_at = max(all_dates) if all_dates else None

    if last_activity_at is not None:
        iso_str, ts_ms = normalize_datetime(last_activity_at)
        neo4j_session.run(
            "MATCH (r:BitbucketRepository{id: $RepoId}) SET r.last_activity_at = $LastActivity, r.last_activity_at_timestamp = $LastActivityTs",
            RepoId=repo_id,
            LastActivity=iso_str,
            LastActivityTs=ts_ms,
        )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("bitbucket_workspace_repositories_cleanup.json", neo4j_session, common_job_parameters)


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
    logger.info(
        "BEGIN Syncing Bitbucket Repositories",
        extra={"workspace": common_job_parameters["WORKSPACE_ID"], "slug": workspace_name, "start": tic},
    )

    logger.info("Syncing Bitbucket All Repositories")
    workspace_repos = get_repos(bitbucket_access_token, workspace_name)
    transformed_data = transform_repos(workspace_repos, workspace_name)

    # Load repositories
    load_repositories_data(neo4j_session, transformed_data["repos"], common_job_parameters)

    # Sync branches for each repository
    for repo in transformed_data["repos"]:
        repo_slug = repo.get("slug")
        if not repo_slug:
            next

        branches = get_branches(bitbucket_access_token, workspace_name, repo_slug)
        default_branch = repo.get("default_branch")
        transformed_branches = transform_branches(branches, repo["uuid"], default_branch)
        load_branches(neo4j_session, transformed_branches, common_job_parameters)
        _update_repo_last_activity(neo4j_session, repo["uuid"], transformed_branches, default_branch)

    # Load languages
    load_languages(neo4j_session, common_job_parameters["UPDATE_TAG"], transformed_data["repo_primary_language"])

    cleanup(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(
        "END Syncing Bitbucket Repositories",
        extra={
            "workspace": common_job_parameters["WORKSPACE_ID"],
            "slug": workspace_name,
            "end": toc,
            "duration": f"{toc - tic:0.4f}",
        },
    )
