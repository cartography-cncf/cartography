import configparser
import logging
import time
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from string import Template
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j
import requests
from packaging.requirements import InvalidRequirement
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from cartography.intel.github.util import describe_request_error
from cartography.intel.github.util import fetch_all
from cartography.intel.github.util import get_retry_delay_seconds
from cartography.intel.github.util import is_retryable_request_error
from cartography.util import normalize_datetime
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

GITHUB_ORG_REPOS_PAGINATED_GRAPHQL = """
    query($login: String!, $cursor: String) {
    organization(login: $login)
        {
            url
            login
            repositories(first: 50, after: $cursor){
                pageInfo{
                    endCursor
                    hasNextPage
                }
                nodes{
                    name
                    nameWithOwner
                    primaryLanguage{
                        name
                    }
                    url
                    sshUrl
                    createdAt
                    description
                    updatedAt
                    pushedAt
                    homepageUrl
                    languages(first: 25){
                        totalCount
                        nodes{
                            name
                        }
                    }
                    defaultBranchRef{
                        name
                        id
                    }
                    refs(first: 100, refPrefix: "refs/heads/", after: null) {
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                        edges {
                            node {
                                name
                                id
                                target {
                                    ... on Commit {
                                        pushedDate
                                    }
                                }
                            }
                        }
                    }
                    isPrivate
                    visibility
                    isArchived
                    isDisabled
                    isLocked
                    owner{
                        url
                        login
                        __typename
                    }
                    collaborators(affiliation: OUTSIDE, first: 50) {
                        edges {
                            permission
                        }
                        nodes {
                            url
                            login
                            name
                            email
                            company
                        }
                    }
                    requirements:object(expression: "HEAD:requirements.txt") {
                        ... on Blob {
                            text
                        }
                    }
                    setupCfg:object(expression: "HEAD:setup.cfg") {
                        ... on Blob {
                            text
                        }
                    }
                }
            }
        }
    }
    """
# Note: In the above query, `HEAD` references the default branch.
# See https://stackoverflow.com/questions/48935381/github-graphql-api-default-branch-in-repository


@timeit
def get(token: str, api_url: str, organization: str) -> List[Dict]:
    """
    Retrieve a list of repos from a Github organization as described in
    https://docs.github.com/en/graphql/reference/objects#repository.
    :param token: The Github API token as string.
    :param api_url: The Github v4 API endpoint as string.
    :param organization: The name of the target Github organization as string.
    :return: A list of dicts representing repos. See tests.data.github.repos for data shape.
    """
    # # TODO: link the Github organization to the repositories
    # try:
    #     repos, _ = fetch_all(
    #         token,
    #         api_url,
    #         organization,
    #         GITHUB_ORG_REPOS_PAGINATED_GRAPHQL,
    #         "repositories",
    #     )
    #     return repos.nodes
    # except requests.exceptions.RequestException as err:
    #     if not is_retryable_request_error(err):
    #         raise

    #     logger.info(
    #         (
    #             f"GitHub GraphQL repository sync failed for org `{organization}` "
    #             f"with {describe_request_error(err)}; falling back to REST repository listing."
    #         ),
    #         exc_info=True,
    #     )

    rest_repos = get_org_repos(organization, token, api_url)
    return [_normalize_rest_repo(rest_repo) for rest_repo in rest_repos]


def transform(repos_json: List[Dict]) -> Dict:
    """
    Parses the JSON returned from GitHub API to create data for graph ingestion
    :param repos_json: the list of individual repository nodes from GitHub. See tests.data.github.repos.GET_REPOS for
    data shape.
    :return: Dict containing the repos, repo->language mapping, owners->repo mapping, outside collaborators->repo
    mapping, and Python requirements files (if any) in a repo.
    """
    transformed_repo_list: List[Dict] = []
    transformed_repo_languages: List[Dict] = []
    transformed_repo_owners: List[Dict] = []
    # See https://docs.github.com/en/graphql/reference/enums#repositorypermission
    transformed_collaborators: Dict[str, List[Any]] = {
        "ADMIN": [],
        "MAINTAIN": [],
        "READ": [],
        "TRIAGE": [],
        "WRITE": [],
    }
    transformed_requirements_files: List[Dict] = []
    transformed_branches: List[Dict] = []
    for repo_object in repos_json:
        _transform_repo_languages(repo_object["url"], repo_object, transformed_repo_languages)
        _transform_repo_objects(repo_object, transformed_repo_list)
        _transform_repo_owners(repo_object["owner"]["url"], repo_object, transformed_repo_owners)
        _transform_collaborators(repo_object.get("collaborators"), repo_object["url"], transformed_collaborators)
        _transform_branches(repo_object["url"], repo_object, transformed_branches)
        # _transform_requirements_txt(repo_object["requirements"], repo_object["url"], transformed_requirements_files)
        # _transform_setup_cfg_requirements(repo_object["setupCfg"], repo_object["url"], transformed_requirements_files)

    # Compute last_activity_at per repo from branch commit timestamps
    # Priority: (1) default branch commit date, (2) max across all branches
    branches_by_repo: Dict[str, List[Dict]] = {}
    for b in transformed_branches:
        branches_by_repo.setdefault(b["repo_id"], []).append(b)

    for repo in transformed_repo_list:
        default_branch_name = repo.get("default_branch")
        repo_branches = branches_by_repo.get(repo["id"], [])
        last_activity_at = None
        if default_branch_name:
            for b in repo_branches:
                if b["name"] == default_branch_name and b.get("last_commit_timestamp"):
                    last_activity_at = b["last_commit_timestamp"]
                    break

        if last_activity_at is None:
            all_dates = [b["last_commit_timestamp"] for b in repo_branches if b.get("last_commit_timestamp")]
            last_activity_at = max(all_dates) if all_dates else None

        # Fall back to repo's updatedAt when no branch commit timestamps are available
        # (pushedDate is null for commits not created via a GitHub push event)
        if last_activity_at is None:
            last_activity_at = repo.get("pushedat") or repo.get("updatedat")

        iso_str, ts_ms = normalize_datetime(last_activity_at)
        repo["last_activity_at"] = iso_str
        repo["last_activity_at_timestamp"] = ts_ms

    results = {
        "repos": transformed_repo_list,
        "repo_languages": transformed_repo_languages,
        "repo_owners": transformed_repo_owners,
        "repo_collaborators": transformed_collaborators,
        "python_requirements": transformed_requirements_files,
        "branches": transformed_branches,
    }
    return results


def _transform_branches(repo_url: str, repo: Dict, transformed_branches: List[Dict]) -> None:
    """
    Transform branch data and filter to include only:
    - Branches active in the last 90 days
    - Default branch (always included)
    """
    if not repo.get("refs"):
        return

    default_branch = repo.get("defaultBranchRef", {}).get("name") if repo.get("defaultBranchRef") else None
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)

    for edge in (repo["refs"].get("edges") or []):
        node = edge["node"]
        branch_name = node["name"]
        target = node.get("target")
        pushed_date_str = target.get("pushedDate") if target else None

        # Always include default branch
        if branch_name == default_branch:
            transformed_branches.append({
                "repo_id": repo_url,
                "branch_id": f"{repo_url}:{node['id']}",
                "name": branch_name,
                "last_commit_timestamp": pushed_date_str,
            })
            continue

        # Filter by activity date
        if pushed_date_str:
            pushed_date = datetime.fromisoformat(pushed_date_str.replace('Z', '+00:00'))
            if pushed_date >= cutoff_date:
                transformed_branches.append({
                    "repo_id": repo_url,
                    "branch_id": f"{repo_url}:{node['id']}",
                    "name": branch_name,
                    "last_commit_timestamp": pushed_date_str,
                })
        else:
            # No date available, include the branch
            transformed_branches.append({
                "repo_id": repo_url,
                "branch_id": f"{repo_url}:{node['id']}",
                "name": branch_name,
                "last_commit_timestamp": pushed_date_str,
            })


def _create_default_branch_id(repo_url: str, default_branch_ref_id: str) -> str:
    """
    Return a unique node id for a repo's defaultBranchId using the given repo_url and default_branch_ref_id.
    This ensures that default branches for each GitHub repo are unique nodes in the graph.
    """
    return f"{repo_url}:{default_branch_ref_id}"


def _create_git_url_from_ssh_url(ssh_url: str) -> str:
    """
    Return a git:// URL from the given ssh_url
    """
    return ssh_url.replace("/", ":").replace("git@", "git://")


def _transform_repo_objects(input_repo_object: Dict, out_repo_list: List[Dict]) -> None:
    """
    Performs data transforms including creating necessary IDs for unique nodes in the graph related to GitHub repos,
    their default branches, and languages.
    :param input_repo_object: A repository node from GitHub; see tests.data.github.repos.GET_REPOS for data shape.
    :param out_repo_list: Out-param to append transformed repos to.
    :return: Nothing
    """
    # Create a unique ID for a GitHubBranch node representing the default branch of this repo object.
    dbr = input_repo_object["defaultBranchRef"]
    default_branch_name = dbr["name"] if dbr else None
    default_branch_id = (
        _create_default_branch_id(input_repo_object["url"], dbr["id"])
        if dbr and dbr.get("id")
        else None
    )

    # Create a git:// URL from the given SSH URL, if it exists.
    ssh_url = input_repo_object.get("sshUrl")
    git_url = _create_git_url_from_ssh_url(ssh_url) if ssh_url else None
    visibility = input_repo_object.get("visibility")
    if visibility is None:
        visibility = "private" if input_repo_object["isPrivate"] else "public"

    out_repo_list.append(
        {
            "id": input_repo_object["url"],
            "createdat": input_repo_object["createdAt"],
            "name": input_repo_object["name"],
            "fullname": input_repo_object["nameWithOwner"],
            "description": input_repo_object["description"],
            "primary_language": (
                input_repo_object["primaryLanguage"]["name"] if input_repo_object.get("primaryLanguage") else ""
            ).lower(),
            "homepage": input_repo_object["homepageUrl"],
            "default_branch": default_branch_name,
            "defaultbranchid": default_branch_id,
            "is_private": input_repo_object["isPrivate"],
            "visibility": visibility,
            "disabled": input_repo_object["isDisabled"],
            "archived": input_repo_object["isArchived"],
            "locked": input_repo_object["isLocked"],
            "giturl": git_url,
            "url": input_repo_object["url"],
            "sshurl": ssh_url,
            "updatedat": input_repo_object["updatedAt"],
            "pushedat": input_repo_object["pushedAt"],
        },
    )


def _transform_repo_owners(owner_id: str, repo: Dict, repo_owners: List[Dict]) -> None:
    """
    Helper function to transform repo owners.
    :param owner_id: The URL of the owner object (either of type Organization or User).
    :param repo: The repo object; see tests.data.github.repos.GET_REPOS for data shape.
    :param repo_owners: Output array to append transformed results to.
    :return: Nothing.
    """
    repo_owners.append(
        {
            "repo_id": repo["url"],
            "owner": repo["owner"]["login"],
            "owner_id": owner_id,
            "type": repo["owner"]["__typename"],
        },
    )


def _transform_repo_languages(repo_url: str, repo: Dict, repo_languages: List[Dict]) -> None:
    """
    Helper function to transform the languages in a GitHub repo.
    :param repo_url: The URL of the repo.
    :param repo: The repo object; see tests.data.github.repos.GET_REPOS for data shape.
    :param repo_languages: Output array to append transformed results to.
    :return: Nothing.
    """
    if repo.get("languages") and repo["languages"]["totalCount"] > 0:
        for language in repo["languages"]["nodes"]:
            repo_languages.append(
                {
                    "repo_id": repo_url,
                    "language_name": language["name"],
                },
            )


def _transform_collaborators(collaborators: Dict, repo_url: str, transformed_collaborators: Dict) -> None:
    """
    Performs data adjustments for outside collaborators in a GitHub repo.
    Output data shape = [{permission, repo_url, url (the user's URL), login, name}, ...]
    :param collaborators: See cartography.tests.data.github.repos for data shape.
    :param repo_url: The URL of the GitHub repo.
    :param transformed_collaborators: Output dict. Data shape =
    {'ADMIN': [{ user }, ...], 'MAINTAIN': [{ user }, ...], 'READ': [ ... ], 'TRIAGE': [ ... ], 'WRITE': [ ... ]}
    :return: Nothing.
    """
    # `collaborators` is sometimes None
    if collaborators:
        for idx, user in enumerate(collaborators["nodes"]):
            user_permission = collaborators["edges"][idx]["permission"]
            user["repo_url"] = repo_url
            transformed_collaborators[user_permission].append(user)


def _transform_requirements_txt(
    req_file_contents: Optional[Dict],
    repo_url: str,
    out_requirements_files: List[Dict],
) -> None:
    """
    Performs data transformations for the requirements.txt file in a GitHub repo, if available.
    :param req_file_contents: Dict: The contents of the requirements.txt file.
    :param repo_url: str: The URL of the GitHub repo.
    :param out_requirements_files: Output array to append transformed results to.
    :return: Nothing.
    """
    if req_file_contents and req_file_contents.get("text"):
        text_contents = req_file_contents["text"]
        requirements_list = text_contents.split("\n")
        _transform_python_requirements(requirements_list, repo_url, out_requirements_files)


def _transform_setup_cfg_requirements(
    setup_cfg_contents: Optional[Dict],
    repo_url: str,
    out_requirements_files: List[Dict],
) -> None:
    """
    Performs data transformations for the setup.cfg file in a GitHub repo, if available.
    :param setup_cfg_contents: Dict: Contains contents of a repo's setup.cfg file.
    :param repo_url: str: The URL of the GitHub repo.
    :param out_requirements_files: Output array to append transformed results to.
    :return: Nothing.
    """
    if not setup_cfg_contents or not setup_cfg_contents.get("text"):
        return
    text_contents = setup_cfg_contents["text"]
    setup_cfg = configparser.ConfigParser()
    try:
        setup_cfg.read_string(text_contents)
    except configparser.Error:
        logger.info(
            f"Failed to parse {repo_url}'s setup.cfg; skipping.",
            exc_info=True,
        )
        return
    requirements_list = parse_setup_cfg(setup_cfg)
    _transform_python_requirements(requirements_list, repo_url, out_requirements_files)


def _transform_python_requirements(
    requirements_list: List[str],
    repo_url: str,
    out_requirements_files: List[Dict],
) -> None:
    """
    Helper function to perform data transformations on an arbitrary list of requirements.
    :param requirements_list: List[str]: List of requirements
    :param repo_url: str: The URL of the GitHub repo.
    :param out_requirements_files: Output array to append transformed results to.
    :return: Nothing.
    """
    parsed_list = []
    for line in requirements_list:
        stripped_line = line.partition("#")[0].strip()
        if stripped_line == "":
            continue
        try:
            req = Requirement(stripped_line)
            parsed_list.append(req)
        except InvalidRequirement:
            # INFO and not WARN/ERROR as we intentionally don't support all ways to specify Python requirements
            logger.info(
                f'Failed to parse line "{line}" in repo {repo_url}\'s requirements.txt; skipping line.',
                exc_info=True,
            )

    for req in parsed_list:
        pinned_version = None
        if len(req.specifier) == 1:
            specifier = next(iter(req.specifier))
            if specifier.operator == "==":
                pinned_version = specifier.version

        # Set `spec` to a default value. Example values for str(req.specifier): "<4.0,>=3.0" or "==1.0.0".
        spec: Optional[str] = str(req.specifier)
        # Set spec to `None` instead of empty string so that the Neo4j driver will leave the library.specifier field
        # undefined. As convention, we prefer undefined values over empty strings in the graph.
        if spec == "":
            spec = None

        canon_name = canonicalize_name(req.name)
        requirement_id = f"{canon_name}|{pinned_version}" if pinned_version else canon_name

        out_requirements_files.append(
            {
                "id": requirement_id,
                "name": canon_name,
                "specifier": spec,
                "version": pinned_version,
                "repo_url": repo_url,
            },
        )


def parse_setup_cfg(config: configparser.ConfigParser) -> List[str]:
    reqs: List[str] = []
    reqs.extend(_parse_setup_cfg_requirements(config.get("options", "install_requires", fallback="")))
    reqs.extend(_parse_setup_cfg_requirements(config.get("options", "setup_requires", fallback="")))
    if config.has_section("options.extras_require"):
        for _, val in config.items("options.extras_require"):
            reqs.extend(_parse_setup_cfg_requirements(val))
    return reqs


# logic taken from setuptools:
# https://github.com/pypa/setuptools/blob/f359b8a7608c7f118710af02cb5edab4e6abb942/setuptools/config.py#L241-L258
def _parse_setup_cfg_requirements(reqs: str, separator: str = ";") -> List[str]:
    if "\n" in reqs:
        reqs_list = reqs.splitlines()
    else:
        reqs_list = reqs.split(separator)

    return [req.strip() for req in reqs_list if req.strip()]


@timeit
def load_github_repos(neo4j_session: neo4j.Session, update_tag: int, repo_data: List[Dict]) -> None:
    """
    Ingest the GitHub repository information
    :param neo4j_session: Neo4J session object for server communication
    :param update_tag: Timestamp used to determine data freshness
    :param repo_data: repository data objects
    :return: None
    """
    ingest_repo = """
    UNWIND $RepoData as repository

    MERGE (repo:GitHubRepository{id: repository.id})
    ON CREATE SET repo.firstseen = timestamp(),
    repo.createdat = repository.createdat

    SET repo.name = repository.name,
    repo.fullname = repository.fullname,
    repo.description = repository.description,
    repo.primary_language = repository.primary_language,
    repo.homepage = repository.homepage,
    repo.default_branch = repository.default_branch,
    repo.defaultbranchid = repository.defaultbranchid,
    repo.is_private = repository.is_private,
    repo.visibility = repository.visibility,
    repo.disabled = repository.disabled,
    repo.archived = repository.archived,
    repo.locked = repository.locked,
    repo.giturl = repository.giturl,
    repo.url = repository.url,
    repo.sshurl = repository.sshurl,
    repo.updatedat = repository.updatedat,
    repo.last_activity_at = repository.last_activity_at,
    repo.last_activity_at_timestamp = repository.last_activity_at_timestamp,
    repo.lastupdated = $UpdateTag

    WITH repo
    WHERE repo.default_branch IS NOT NULL AND repo.defaultbranchid IS NOT NULL
    MERGE (branch:GitHubBranch{id: repo.defaultbranchid})
    ON CREATE SET branch.firstseen = timestamp()
    SET branch.name = repo.default_branch,
    branch.lastupdated = $UpdateTag

    MERGE (repo)-[r:BRANCH]->(branch)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """
    neo4j_session.run(
        ingest_repo,
        RepoData=repo_data,
        UpdateTag=update_tag,
    )


@timeit
def load_github_languages(neo4j_session: neo4j.Session, update_tag: int, repo_languages: List[Dict]) -> None:
    """
    Ingest the relationships for repo languages
    :param neo4j_session: Neo4J session object for server communication
    :param update_tag: Timestamp used to determine data freshness
    :param repo_languages: list of language to repo mappings
    :return: Nothing
    """
    ingest_languages = """
        UNWIND $Languages as lang

        MERGE (pl:ProgrammingLanguage{id: lang.language_name})
        ON CREATE SET pl.firstseen = timestamp(),
        pl.name = lang.language_name
        SET pl.lastupdated = $UpdateTag
        WITH pl, lang

        MATCH (repo:GitHubRepository{id: lang.repo_id})
        MERGE (pl)<-[r:LANGUAGE]-(repo)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $UpdateTag"""

    neo4j_session.run(
        ingest_languages,
        Languages=repo_languages,
        UpdateTag=update_tag,
    )


@timeit
def load_github_owners(neo4j_session: neo4j.Session, update_tag: int, repo_owners: List[Dict]) -> None:
    """
    Ingest the relationships for repo owners
    :param neo4j_session: Neo4J session object for server communication
    :param update_tag: Timestamp used to determine data freshness
    :param repo_owners: list of owner to repo mappings
    :return: Nothing
    """
    for owner in repo_owners:
        ingest_owner_template = Template("""
            MERGE (node:$account_type{id: $Id})
            ON CREATE SET node.firstseen = timestamp()
            SET node.username = $UserName,
            node.lastupdated = $UpdateTag
            WITH node

            MATCH (repo:GitHubRepository{id: $RepoId})
            MERGE (node)-[r:RESOURCE]->(repo)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $UpdateTag""")

        # INFO: Only Organization is supported
        # account_type = {'User': "GitHubUser", 'Organization': "GitHubOrganization"}
        account_type = {"Organization": "GitHubOrganization"}

        neo4j_session.run(
            ingest_owner_template.safe_substitute(account_type=account_type[owner["type"]]),
            Id=owner["owner"],
            UserName=owner["owner"],
            RepoId=owner["repo_id"],
            UpdateTag=update_tag,
        )


@timeit
def load_collaborators(neo4j_session: neo4j.Session, update_tag: int, collaborators: Dict) -> None:
    query = Template("""
    UNWIND $UserData as user

    MERGE (u:GitHubUser{id: user.url})
    ON CREATE SET u.firstseen = timestamp()
    SET u.fullname = user.name,
    u.username = user.login,
    u.permission = user.permission,
    u.email = user.email,
    u.company = user.company,
    u.lastupdated = $UpdateTag

    WITH u, user
    MATCH (repo:GitHubRepository{id: user.repo_url})
    MERGE (repo)<-[o:$rel_label]-(u)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = $UpdateTag
    """)
    for collab_type in collaborators.keys():
        relationship_label = f"OUTSIDE_COLLAB_{collab_type}"
        neo4j_session.run(
            query.safe_substitute(rel_label=relationship_label),
            UserData=collaborators[collab_type],
            UpdateTag=update_tag,
        )


@timeit
def load(neo4j_session: neo4j.Session, common_job_parameters: Dict, repo_data: Dict) -> None:
    load_github_repos(neo4j_session, common_job_parameters["UPDATE_TAG"], repo_data["repos"])
    load_github_branches(neo4j_session, common_job_parameters["UPDATE_TAG"], repo_data["branches"])
    load_github_owners(neo4j_session, common_job_parameters["UPDATE_TAG"], repo_data["repo_owners"])
    load_github_languages(neo4j_session, common_job_parameters["UPDATE_TAG"], repo_data["repo_languages"])
    load_collaborators(neo4j_session, common_job_parameters["UPDATE_TAG"], repo_data["repo_collaborators"])
    load_python_requirements(neo4j_session, common_job_parameters["UPDATE_TAG"], repo_data["python_requirements"])


@timeit
def load_github_branches(neo4j_session: neo4j.Session, update_tag: int, branch_data: List[Dict]) -> None:
    """
    Ingest the GitHub branch information
    :param neo4j_session: Neo4J session object for server communication
    :param update_tag: Timestamp used to determine data freshness
    :param branch_data: branch data objects
    :return: None
    """
    ingest_branches = """
    UNWIND $BranchData as branch_info
    MERGE (branch:GitHubBranch{id: branch_info.branch_id})
    ON CREATE SET branch.firstseen = timestamp()
    SET branch.name = branch_info.name,
    branch.last_commit_timestamp = branch_info.last_commit_timestamp,
    branch.lastupdated = $UpdateTag

    WITH branch, branch_info
    MATCH (repo:GitHubRepository{id: branch_info.repo_id})
    MERGE (repo)-[r:BRANCH]->(branch)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """
    neo4j_session.run(
        ingest_branches,
        BranchData=branch_data,
        UpdateTag=update_tag,
    )


@timeit
def load_python_requirements(neo4j_session: neo4j.Session, update_tag: int, requirements_objects: List[Dict]) -> None:
    query = """
    UNWIND $Requirements AS req
        MERGE (lib:PythonLibrary:Dependency{id: req.id})
        ON CREATE SET lib.firstseen = timestamp(),
        lib.name = req.name
        SET lib.lastupdated = $UpdateTag,
        lib.version = req.version

        WITH lib, req
        MATCH (repo:GitHubRepository{id: req.repo_url})
        MERGE (repo)-[r:REQUIRES]->(lib)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $UpdateTag,
        r.specifier = req.specifier
    """
    neo4j_session.run(
        query,
        Requirements=requirements_objects,
        UpdateTag=update_tag,
    )


def _build_org_repos_url(api_url: str, org_name: str) -> str:
    api_root = api_url.rstrip("/")
    for suffix, replacement in (
        ("/api/v3/graphql", "/api/v3"),
        ("/api/graphql", "/api/v3"),
        ("/graphql", ""),
    ):
        if api_root.endswith(suffix):
            api_root = f"{api_root[:-len(suffix)]}{replacement}"
            break

    return f"{api_root}/orgs/{org_name}/repos"


def _normalize_rest_repo(repo: Dict[str, Any]) -> Dict[str, Any]:
    owner = repo.get("owner") or {}
    owner_login = owner.get("login")
    owner_url = owner.get("html_url") or (
        f"https://github.com/{owner_login}" if owner_login else owner.get("url")
    )
    default_branch_name = repo.get("default_branch")

    return {
        "name": repo["name"],
        "nameWithOwner": repo.get("full_name") or repo["name"],
        "primaryLanguage": {"name": repo["language"]} if repo.get("language") else None,
        "url": repo["html_url"],
        "sshUrl": repo.get("ssh_url"),
        "createdAt": repo["created_at"],
        "description": repo.get("description"),
        "updatedAt": repo["updated_at"],
        "pushedAt": repo["pushed_at"],
        "homepageUrl": repo.get("homepage"),
        "languages": {"totalCount": 0, "nodes": []},
        "defaultBranchRef": (
            {"name": default_branch_name, "id": None}
            if default_branch_name
            else None
        ),
        "isPrivate": repo["private"],
        "visibility": repo.get("visibility") or ("private" if repo["private"] else "public"),
        "isArchived": repo.get("archived", False),
        "isDisabled": repo.get("disabled", False),
        "isLocked": repo.get("locked", False),
        "owner": {
            "url": owner_url,
            "login": owner_login,
            "__typename": owner.get("type", "Organization"),
        },
        "collaborators": None,
        "requirements": None,
        "setupCfg": None,
    }


def get_org_repos(org_name: str, access_token: str, api_url: str, retries: int = 5) -> List[Dict[str, Any]]:
    # GitHub API endpoint for listing organization repositories
    url = _build_org_repos_url(api_url, org_name)

    # Headers for authentication and API version
    headers = {"Authorization": f"token {access_token}", "Accept": "application/vnd.github.v3+json"}

    all_repos = []
    page = 1

    while True:
        retry = 0
        repos = None
        while retry < retries:
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    params={"page": page, "per_page": 100},
                    timeout=(60, 60),
                )
                response.raise_for_status()
                repos = response.json()
                break
            except (
                requests.exceptions.Timeout,
                requests.exceptions.HTTPError,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
            ) as err:
                retry += 1
                if retry >= retries or not is_retryable_request_error(err):
                    logger.error(
                        (
                            f"GitHub REST repository fallback failed for org `{org_name}` "
                            f"after {retry} attempts ({describe_request_error(err)})."
                        ),
                        exc_info=True,
                    )
                    raise
                logger.warning(
                    (
                        f"GitHub REST repository fallback retry for org `{org_name}` "
                        f"after {describe_request_error(err)} ({retry}/{retries})."
                    ),
                )
                time.sleep(get_retry_delay_seconds(err, retry))

        if not repos:
            break

        all_repos.extend(repos)
        page += 1

    return all_repos


def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
    github_api_key: str,
    github_url: str,
    organization: str,
) -> None:
    """
    Performs the sequential tasks to collect, transform, and sync github data
    :param neo4j_session: Neo4J session for database interface
    :param common_job_parameters: Common job parameters containing UPDATE_TAG
    :param github_api_key: The API key to access the GitHub v4 API
    :param github_url: The URL for the GitHub v4 endpoint to use
    :param organization: The organization to query GitHub for
    :return: Nothing
    """
    tic = time.perf_counter()
    logger.info("Syncing GitHub Repositories instances in account %s - url %s", organization, github_url)

    # repos_list = get_org_repos(organization, github_api_key)
    repos_json = get(github_api_key, github_url, organization)

    repo_data = transform(repos_json)
    load(neo4j_session, common_job_parameters, repo_data)

    run_cleanup_job("github_repos_cleanup.json", neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process GitHub repositories: {toc - tic:0.4f} seconds")
