import configparser
import logging
from collections import namedtuple
from string import Template
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from packaging.requirements import InvalidRequirement
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from cartography.intel.github.util import fetch_all
from cartography.intel.github.util import PaginatedGraphqlData
from cartography.util import backoff_handler
from cartography.util import retries_with_backoff
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


# Representation of a user's permission level and affiliation to a GitHub repo. See:
# - Permission: https://docs.github.com/en/graphql/reference/enums#repositorypermission
# - Affiliation: https://docs.github.com/en/graphql/reference/enums#collaboratoraffiliation
UserAffiliationAndRepoPermission = namedtuple(
    'UserAffiliationAndRepoPermission',
    [
        'user',  # Dict
        'permission',  # 'WRITE', 'MAINTAIN', 'ADMIN', etc
        'affiliation',  # 'OUTSIDE', 'DIRECT'
    ],
)


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
                    isPrivate
                    isArchived
                    isDisabled
                    isLocked
                    owner{
                        url
                        login
                        __typename
                    }
                    directCollaborators: collaborators(first: 100, affiliation: DIRECT) {
                        totalCount
                    }
                    outsideCollaborators: collaborators(first: 100, affiliation: OUTSIDE) {
                        totalCount
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

GITHUB_REPO_COLLABS_PAGINATED_GRAPHQL = """
    query($login: String!, $repo: String!, $affiliation: CollaboratorAffiliation!, $cursor: String) {
        organization(login: $login) {
            url
            login
            repository(name: $repo){
                name
                collaborators(first: 50, affiliation: $affiliation, after: $cursor) {
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
                    pageInfo{
                        endCursor
                        hasNextPage
                    }
                }
            }
        }
        rateLimit {
            limit
            cost
            remaining
            resetAt
        }
    }
    """


def _get_repo_collaborators_inner_func(
        org: str,
        api_url: str,
        token: str,
        repo_raw_data: list[dict[str, Any]],
        affiliation: str,
        collab_users: list[dict[str, Any]],
        collab_permission: list[str],
) -> dict[str, list[UserAffiliationAndRepoPermission]]:
    result: dict[str, list[UserAffiliationAndRepoPermission]] = {}

    for repo in repo_raw_data:
        repo_name = repo['name']
        repo_url = repo['url']

        if ((affiliation == 'OUTSIDE' and repo['outsideCollaborators']['totalCount'] == 0) or
                (affiliation == 'DIRECT' and repo['directCollaborators']['totalCount'] == 0)):
            # repo has no collabs of the affiliation type we're looking for, so don't waste time making an API call
            result[repo_url] = []
            continue

        logger.info(f"Loading {affiliation} collaborators for repo {repo_name}.")
        collaborators = _get_repo_collaborators(token, api_url, org, repo_name, affiliation)

        # nodes and edges are expected to always be present given that we only call for them if totalCount is > 0
        # however sometimes GitHub returns None, as in issue 1334 and 1404.
        for collab in collaborators.nodes or []:
            collab_users.append(collab)

        # The `or []` is because `.edges` can be None.
        for perm in collaborators.edges or []:
            collab_permission.append(perm['permission'])

        result[repo_url] = [
            UserAffiliationAndRepoPermission(user, permission, affiliation)
            for user, permission in zip(collab_users, collab_permission)
        ]
    return result


def _get_repo_collaborators_for_multiple_repos(
        repo_raw_data: list[dict[str, Any]],
        affiliation: str,
        org: str,
        api_url: str,
        token: str,
) -> dict[str, list[UserAffiliationAndRepoPermission]]:
    """
    For every repo in the given list, retrieve the collaborators.
    :param repo_raw_data: A list of dicts representing repos. See tests.data.github.repos.GET_REPOS for data shape.
    :param affiliation: The type of affiliation to retrieve collaborators for. Either 'DIRECT' or 'OUTSIDE'.
      See https://docs.github.com/en/graphql/reference/enums#collaboratoraffiliation
    :param org: The name of the target Github organization as string.
    :param api_url: The Github v4 API endpoint as string.
    :param token: The Github API token as string.
    :return: A dictionary of repo URL to list of UserAffiliationAndRepoPermission
    """
    logger.info(f'Retrieving repo collaborators for affiliation "{affiliation}" on org "{org}".')
    collab_users: List[dict[str, Any]] = []
    collab_permission: List[str] = []

    result: dict[str, list[UserAffiliationAndRepoPermission]] = retries_with_backoff(
        _get_repo_collaborators_inner_func,
        TypeError,
        5,
        backoff_handler,
    )(
        org=org,
        api_url=api_url,
        token=token,
        repo_raw_data=repo_raw_data,
        affiliation=affiliation,
        collab_users=collab_users,
        collab_permission=collab_permission,
    )
    return result


def _get_repo_collaborators(
        token: str, api_url: str, organization: str, repo: str, affiliation: str,
) -> PaginatedGraphqlData:
    """
    Retrieve a list of collaborators for a given repository, as described in
    https://docs.github.com/en/graphql/reference/objects#repositorycollaboratorconnection.
    :param token: The Github API token as string.
    :param api_url: The Github v4 API endpoint as string.
    :param organization: The name of the target Github organization as string.
    :pram repo: The name of the target Github repository as string.
    :param affiliation: The type of affiliation to retrieve collaborators for. Either 'DIRECT' or 'OUTSIDE'.
      See https://docs.github.com/en/graphql/reference/enums#collaboratoraffiliation
    :return: A list of dicts representing repos. See tests.data.github.repos for data shape.
    """
    collaborators, _ = fetch_all(
        token,
        api_url,
        organization,
        GITHUB_REPO_COLLABS_PAGINATED_GRAPHQL,
        'repository',
        resource_inner_type='collaborators',
        repo=repo,
        affiliation=affiliation,
    )
    return collaborators


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
    # TODO: link the Github organization to the repositories
    repos, _ = fetch_all(
        token,
        api_url,
        organization,
        GITHUB_ORG_REPOS_PAGINATED_GRAPHQL,
        'repositories',
    )
    return repos.nodes


def transform(
        repos_json: List[Dict],
        direct_collaborators: dict[str, List[UserAffiliationAndRepoPermission]],
        outside_collaborators: dict[str, List[UserAffiliationAndRepoPermission]],
) -> Dict:
    """
    Parses the JSON returned from GitHub API to create data for graph ingestion
    :param repos_json: the list of individual repository nodes from GitHub.
        See tests.data.github.repos.GET_REPOS for data shape.
    :param direct_collaborators: dict of repo URL to list of direct collaborators.
        See tests.data.github.repos.DIRECT_COLLABORATORS for data shape.
    :param outside_collaborators: dict of repo URL to list of outside collaborators.
        See tests.data.github.repos.OUTSIDE_COLLABORATORS for data shape.
    :return: Dict containing the repos, repo->language mapping, owners->repo mapping, outside collaborators->repo
    mapping, and Python requirements files (if any) in a repo.
    """
    transformed_repo_list: List[Dict] = []
    transformed_repo_languages: List[Dict] = []
    transformed_repo_owners: List[Dict] = []
    # See https://docs.github.com/en/graphql/reference/enums#repositorypermission
    transformed_outside_collaborators: Dict[str, List[Any]] = {
        'ADMIN': [], 'MAINTAIN': [], 'READ': [], 'TRIAGE': [], 'WRITE': [],
    }
    transformed_direct_collaborators: Dict[str, List[Any]] = {
        'ADMIN': [], 'MAINTAIN': [], 'READ': [], 'TRIAGE': [], 'WRITE': [],
    }
    transformed_requirements_files: List[Dict] = []
    for repo_object in repos_json:
        _transform_repo_languages(repo_object['url'], repo_object, transformed_repo_languages)
        _transform_repo_objects(repo_object, transformed_repo_list)
        _transform_repo_owners(repo_object['owner']['url'], repo_object, transformed_repo_owners)

        # Allow sync to continue if we didn't have permissions to list collaborators
        repo_url = repo_object['url']
        if repo_url in outside_collaborators:
            _transform_collaborators(
                repo_object['url'],
                outside_collaborators[repo_object['url']],
                transformed_outside_collaborators,
            )
        if repo_url in direct_collaborators:
            _transform_collaborators(
                repo_object['url'],
                direct_collaborators[repo_object['url']],
                transformed_direct_collaborators,
            )

        _transform_requirements_txt(repo_object['requirements'], repo_url, transformed_requirements_files)
        _transform_setup_cfg_requirements(repo_object['setupCfg'], repo_url, transformed_requirements_files)
    results = {
        'repos': transformed_repo_list,
        'repo_languages': transformed_repo_languages,
        'repo_owners': transformed_repo_owners,
        'repo_outside_collaborators': transformed_outside_collaborators,
        'repo_direct_collaborators': transformed_direct_collaborators,
        'python_requirements': transformed_requirements_files,
    }
    return results


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
    dbr = input_repo_object['defaultBranchRef']
    default_branch_name = dbr['name'] if dbr else None
    default_branch_id = _create_default_branch_id(input_repo_object['url'], dbr['id']) if dbr else None

    # Create a git:// URL from the given SSH URL, if it exists.
    ssh_url = input_repo_object.get('sshUrl')
    git_url = _create_git_url_from_ssh_url(ssh_url) if ssh_url else None

    out_repo_list.append({
        'id': input_repo_object['url'],
        'createdat': input_repo_object['createdAt'],
        'name': input_repo_object['name'],
        'fullname': input_repo_object['nameWithOwner'],
        'description': input_repo_object['description'],
        'primarylanguage': input_repo_object['primaryLanguage'],
        'homepage': input_repo_object['homepageUrl'],
        'defaultbranch': default_branch_name,
        'defaultbranchid': default_branch_id,
        'private': input_repo_object['isPrivate'],
        'disabled': input_repo_object['isDisabled'],
        'archived': input_repo_object['isArchived'],
        'locked': input_repo_object['isLocked'],
        'giturl': git_url,
        'url': input_repo_object['url'],
        'sshurl': ssh_url,
        'updatedat': input_repo_object['updatedAt'],
    })


def _transform_repo_owners(owner_id: str, repo: Dict, repo_owners: List[Dict]) -> None:
    """
    Helper function to transform repo owners.
    :param owner_id: The URL of the owner object (either of type Organization or User).
    :param repo: The repo object; see tests.data.github.repos.GET_REPOS for data shape.
    :param repo_owners: Output array to append transformed results to.
    :return: Nothing.
    """
    repo_owners.append({
        'repo_id': repo['url'],
        'owner': repo['owner']['login'],
        'owner_id': owner_id,
        'type': repo['owner']['__typename'],
    })


def _transform_repo_languages(repo_url: str, repo: Dict, repo_languages: List[Dict]) -> None:
    """
    Helper function to transform the languages in a GitHub repo.
    :param repo_url: The URL of the repo.
    :param repo: The repo object; see tests.data.github.repos.GET_REPOS for data shape.
    :param repo_languages: Output array to append transformed results to.
    :return: Nothing.
    """
    if repo['languages']['totalCount'] > 0:
        for language in repo['languages']['nodes']:
            repo_languages.append({
                'repo_id': repo_url,
                'language_name': language['name'],
            })


def _transform_collaborators(
        repo_url: str, collaborators: List[UserAffiliationAndRepoPermission], transformed_collaborators: Dict,
) -> None:
    """
    Performs data adjustments for collaborators in a GitHub repo.
    Output data shape = [{permission, repo_url, url (the user's URL), login, name}, ...]
    :param collaborators: For data shape, see
        cartography.tests.data.github.repos.DIRECT_COLLABORATORS
        cartography.tests.data.github.repos.OUTSIDE_COLLABORATORS
    :param repo_url: The URL of the GitHub repo.
    :param transformed_collaborators: Output dict. Data shape =
    {'ADMIN': [{ user }, ...], 'MAINTAIN': [{ user }, ...], 'READ': [ ... ], 'TRIAGE': [ ... ], 'WRITE': [ ... ]}
    :return: Nothing.
    """
    # `collaborators` is sometimes None
    if collaborators:
        for collaborator in collaborators:
            user = collaborator.user
            user['repo_url'] = repo_url
            user['affiliation'] = collaborator.affiliation
            transformed_collaborators[collaborator.permission].append(user)


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
    if req_file_contents and req_file_contents.get('text'):
        text_contents = req_file_contents['text']
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
    if not setup_cfg_contents or not setup_cfg_contents.get('text'):
        return
    text_contents = setup_cfg_contents['text']
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
        stripped_line = line.partition('#')[0].strip()
        if stripped_line == '':
            continue
        try:
            req = Requirement(stripped_line)
            parsed_list.append(req)
        except InvalidRequirement:
            # INFO and not WARN/ERROR as we intentionally don't support all ways to specify Python requirements
            logger.info(
                f"Failed to parse line \"{line}\" in repo {repo_url}'s requirements.txt; skipping line.",
                exc_info=True,
            )

    for req in parsed_list:
        pinned_version = None
        if len(req.specifier) == 1:
            specifier = next(iter(req.specifier))
            if specifier.operator == '==':
                pinned_version = specifier.version

        # Set `spec` to a default value. Example values for str(req.specifier): "<4.0,>=3.0" or "==1.0.0".
        spec: Optional[str] = str(req.specifier)
        # Set spec to `None` instead of empty string so that the Neo4j driver will leave the library.specifier field
        # undefined. As convention, we prefer undefined values over empty strings in the graph.
        if spec == '':
            spec = None

        canon_name = canonicalize_name(req.name)
        requirement_id = f"{canon_name}|{pinned_version}" if pinned_version else canon_name

        out_requirements_files.append({
            "id": requirement_id,
            "name": canon_name,
            "specifier": spec,
            "version": pinned_version,
            "repo_url": repo_url,
        })


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
    repo.primarylanguage = repository.primarylanguage.name,
    repo.homepage = repository.homepage,
    repo.defaultbranch = repository.defaultbranch,
    repo.defaultbranchid = repository.defaultbranchid,
    repo.private = repository.private,
    repo.disabled = repository.disabled,
    repo.archived = repository.archived,
    repo.locked = repository.locked,
    repo.giturl = repository.giturl,
    repo.url = repository.url,
    repo.sshurl = repository.sshurl,
    repo.updatedat = repository.updatedat,
    repo.lastupdated = $UpdateTag

    WITH repo
    WHERE repo.defaultbranch IS NOT NULL AND repo.defaultbranchid IS NOT NULL
    MERGE (branch:GitHubBranch{id: repo.defaultbranchid})
    ON CREATE SET branch.firstseen = timestamp()
    SET branch.name = repo.defaultbranch,
    branch.lastupdated = $UpdateTag

    MERGE (repo)-[r:BRANCH]->(branch)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = r.UpdateTag
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
            MERGE (user:$account_type{id: $Id})
            ON CREATE SET user.firstseen = timestamp()
            SET user.username = $UserName,
            user.lastupdated = $UpdateTag
            WITH user

            MATCH (repo:GitHubRepository{id: $RepoId})
            MERGE (user)<-[r:OWNER]-(repo)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $UpdateTag""")

        account_type = {'User': "GitHubUser", 'Organization': "GitHubOrganization"}

        neo4j_session.run(
            ingest_owner_template.safe_substitute(account_type=account_type[owner['type']]),
            Id=owner['owner_id'],
            UserName=owner['owner'],
            RepoId=owner['repo_id'],
            UpdateTag=update_tag,
        )


@timeit
def load_collaborators(neo4j_session: neo4j.Session, update_tag: int, collaborators: Dict, affiliation: str) -> None:
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
        relationship_label = f"{affiliation}_COLLAB_{collab_type}"
        neo4j_session.run(
            query.safe_substitute(rel_label=relationship_label),
            UserData=collaborators[collab_type],
            UpdateTag=update_tag,
        )


@timeit
def load(neo4j_session: neo4j.Session, common_job_parameters: Dict, repo_data: Dict) -> None:
    load_github_repos(neo4j_session, common_job_parameters['UPDATE_TAG'], repo_data['repos'])
    load_github_owners(neo4j_session, common_job_parameters['UPDATE_TAG'], repo_data['repo_owners'])
    load_github_languages(neo4j_session, common_job_parameters['UPDATE_TAG'], repo_data['repo_languages'])
    load_collaborators(
        neo4j_session, common_job_parameters['UPDATE_TAG'], repo_data['repo_direct_collaborators'], 'DIRECT',
    )
    load_collaborators(
        neo4j_session, common_job_parameters['UPDATE_TAG'], repo_data['repo_outside_collaborators'], 'OUTSIDE',
    )
    load_python_requirements(neo4j_session, common_job_parameters['UPDATE_TAG'], repo_data['python_requirements'])


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
    logger.info("Syncing GitHub repos")
    repos_json = get(github_api_key, github_url, organization)
    direct_collabs: dict[str, list[UserAffiliationAndRepoPermission]] = {}
    outside_collabs: dict[str, list[UserAffiliationAndRepoPermission]] = {}
    try:
        direct_collabs = _get_repo_collaborators_for_multiple_repos(
            repos_json, "DIRECT", organization, github_url, github_api_key,
        )
        outside_collabs = _get_repo_collaborators_for_multiple_repos(
            repos_json, "OUTSIDE", organization, github_url, github_api_key,
        )
    except TypeError:
        # due to permission errors or transient network error or some other nonsense
        logger.warning('Unable to list repo collaborators due to permission errors; continuing on.', exc_info=True)
    repo_data = transform(repos_json, direct_collabs, outside_collabs)
    load(neo4j_session, common_job_parameters, repo_data)
    run_cleanup_job('github_repos_cleanup.json', neo4j_session, common_job_parameters)
