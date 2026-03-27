import logging
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from typing import Dict
from typing import List

import neo4j

from .util import call_azure_devops_api_pagination
from .util import validate_repository_data
from cartography.util import normalize_datetime
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_repositories_for_project(
    api_url: str,
    organization_name: str,
    project_id: str,
    access_token: str,
) -> List[Dict]:
    """
    Retrieve a list of repositories from the given Azure DevOps project.

    Args:
        api_url: Base Azure DevOps URL (e.g., https://dev.azure.com)
        organization_name: Name of the organization
        project_id: ID of the project
        access_token: Microsoft Entra ID OAuth access token

    Returns:
        List of repository dictionaries or empty list if failed
    """
    url = f"{api_url}/{organization_name}/{project_id}/_apis/git/repositories"
    params = {"api-version": "7.1"}

    logger.debug(f"Fetching all repositories for project {project_id} from: {url}")
    repos = call_azure_devops_api_pagination(url, access_token, params)

    if not repos:
        logger.warning(f"No response received for repositories in project {project_id}")
        return []

    # Filter out invalid repositories
    valid_repos = [r for r in repos if validate_repository_data(r)]

    if len(valid_repos) != len(repos):
        logger.warning(
            f"Filtered out {len(repos) - len(valid_repos)} invalid repositories for project {project_id}",
        )

    logger.debug(
        f"Retrieved {len(valid_repos)} valid repositories for project {project_id}",
    )
    return valid_repos


@timeit
def get_branches_for_repository(
    api_url: str,
    organization_name: str,
    project_id: str,
    repository_id: str,
    access_token: str,
) -> List[Dict]:
    """
    Retrieve a list of branches for the given Azure DevOps repository.
    """
    url = f"{api_url}/{organization_name}/{project_id}/_apis/git/repositories/{repository_id}/stats/branches"
    params = {"api-version": "7.1"}
    branches = call_azure_devops_api_pagination(url, access_token, params)
    return branches


@timeit
def load_repositories(
    neo4j_session: neo4j.Session,
    repo_data: List[Dict],
    project_id: str,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Load Azure DevOps repository data into Neo4j with comprehensive properties.
    - id: Repository ID (unique identifier)
    - name: Repository name
    - url: Repository URL
    - sshUrl: SSH clone URL
    - remoteUrl: Remote URL
    - state: Repository state
    - size: Repository size in bytes
    - defaultBranch: Default branch name
    - isDisabled: Whether repository is disabled
    - webUrl: Web interface URL
    - project: Associated project information
    - is_private: Boolean indicating if the repository is private
    - last_activity_at: Last activity timestamp
    - last_activity_at_timestamp: Last activity timestamp in milliseconds
    """
    query = """
    UNWIND $RepoData as repo

    MERGE (r:AzureDevOpsRepo{id: repo.id})
    ON CREATE SET r.firstseen = timestamp()
    SET r.name = repo.name,
        r.url = repo.url,
        r.sshurl = repo.sshUrl,
        r.remoteurl = repo.remoteUrl,
        r.state = repo.state,
        r.size = repo.size,
        r.default_branch = repo.defaultBranch,
        r.isdisabled = repo.isDisabled,
        r.archived = repo.isDisabled,
        r.weburl = repo.webUrl,
        r.project = repo.project.name,
        r.visibility = repo.project_visibility,
        r.is_private = CASE WHEN repo.project_visibility = 'private' THEN true ELSE false END,
        r.primary_language = repo.primary_language,
        r.lastupdated = $UpdateTag
    WITH r

    MATCH (p:AzureDevOpsProject{id: $ProjectId})
    MERGE (p)-[rel:HAS_REPO]->(r)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $UpdateTag
    """
    neo4j_session.run(
        query,
        RepoData=repo_data,
        ProjectId=project_id,
        UpdateTag=common_job_parameters["UPDATE_TAG"],
    )


def transform_branches_data(branches: List[Dict], repo_id: str, default_branch: str = None) -> List[Dict]:
    """
    Transform branch data and filter to include only:
    - Branches active in the last 90 days
    - Default branch (always included)
    """
    transformed_branches = []
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)

    for branch in branches:
        branch_name = branch["name"]
        commit = branch.get("commit", {})
        committer = commit.get("committer", {})
        commit_date_str = committer.get("date")

        # Always include default branch
        if default_branch and branch_name == default_branch:
            transformed_branches.append({
                "repo_id": repo_id,
                "id": f"{repo_id}:{branch_name}",
                "name": branch_name,
                "commitDate": commit_date_str,
            })
            continue

        # Filter by activity date
        if commit_date_str:
            commit_date = datetime.fromisoformat(commit_date_str.replace('Z', '+00:00'))
            if commit_date >= cutoff_date:
                transformed_branches.append({
                    "repo_id": repo_id,
                    "id": f"{repo_id}:{branch_name}",
                    "name": branch_name,
                    "commitDate": commit_date_str,
                })
        else:
            # No date available, include the branch
            transformed_branches.append({
                "repo_id": repo_id,
                "id": f"{repo_id}:{branch_name}",
                "name": branch_name,
                "commitDate": commit_date_str,
            })

    return transformed_branches


@timeit
def load_branches_data(
    neo4j_session: neo4j.Session,
    branches_data: List[Dict],
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Load Azure DevOps branch data into Neo4j.
    """
    query = """
    UNWIND $BranchesData as branch
    MERGE (b:AzureDevOpsBranch{id: branch.id})
    ON CREATE SET b.firstseen = timestamp()
    SET b.name = branch.name,
        b.commitDate = branch.commitDate,
        b.lastupdated = $UpdateTag
    WITH b, branch

    MATCH (r:AzureDevOpsRepo{id: branch.repo_id})
    MERGE (r)-[rel:BRANCH]->(b)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $UpdateTag
    """
    neo4j_session.run(
        query,
        BranchesData=branches_data,
        UpdateTag=common_job_parameters["UPDATE_TAG"],
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        "azure_devops_repos_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


def _update_repo_last_activity(
    neo4j_session: neo4j.Session,
    repo_id: str,
    branches: List[Dict],
    default_branch: str = None,
) -> None:
    """
    Compute and store last_activity_at for an Azure DevOps repository from its branch commit dates.
    Priority: (1) default branch commit date, (2) max commit date across all branches.
    """
    last_activity_at = None
    # Priority 1: default branch commit date
    if default_branch:
        for b in branches:
            if b["name"] == default_branch and b.get("commitDate"):
                last_activity_at = b["commitDate"]
                break

    # Priority 2: max across all branches
    if last_activity_at is None:
        all_dates = [b["commitDate"] for b in branches if b.get("commitDate")]
        last_activity_at = max(all_dates) if all_dates else None

    if last_activity_at is not None:
        iso_str, ts_ms = normalize_datetime(last_activity_at)
        neo4j_session.run(
            "MATCH (r:AzureDevOpsRepo{id: $RepoId}) SET r.last_activity_at = $LastActivity, r.last_activity_at_timestamp = $LastActivityTs",
            RepoId=repo_id,
            LastActivity=iso_str,
            LastActivityTs=ts_ms,
        )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
    access_token: str,
    azure_devops_url: str,
    organization_name: str,
    projects: List[Dict],
) -> None:
    """
    Syncs the repositories for the given list of projects.
    """
    logger.info(
        f"Syncing repositories for {len(projects)} projects in organization '{organization_name}'",
    )

    for project in projects:
        project_id = project["id"]
        logger.info(f"Syncing repositories for project '{project['name']}'")
        repos = get_repositories_for_project(
            azure_devops_url,
            organization_name,
            project_id,
            access_token,
        )
        if repos:
            project_visibility = project.get("visibility")
            for repo in repos:
                # Normalize defaultBranch: strip refs/heads/ prefix
                raw_db = repo.get("defaultBranch") or ""
                repo["defaultBranch"] = raw_db.replace("refs/heads/", "") if raw_db.startswith("refs/heads/") else raw_db
                # Inherit visibility from project (not available on repo API response)
                repo["project_visibility"] = project_visibility
                # primary_language not available in Azure DevOps API
                repo["primary_language"] = None

            load_repositories(neo4j_session, repos, project_id, common_job_parameters)

            # Sync branches for each repository and compute last activity date
            for repo in repos:
                branches = get_branches_for_repository(
                    azure_devops_url,
                    organization_name,
                    project_id,
                    repo["id"],
                    access_token,
                )
                if branches:
                    default_branch = repo.get("defaultBranch")  # already normalized above
                    transformed_branches = transform_branches_data(branches, repo["id"], default_branch)
                    load_branches_data(neo4j_session, transformed_branches, common_job_parameters)
                    _update_repo_last_activity(neo4j_session, repo["id"], transformed_branches, default_branch)

    cleanup(neo4j_session, common_job_parameters)
