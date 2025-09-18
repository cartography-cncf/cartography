import configparser
import logging
from collections import defaultdict
from collections import namedtuple
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from packaging.requirements import InvalidRequirement
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from cartography.client.core.tx import load as load_data
from cartography.graph.job import GraphJob
from cartography.intel.github.util import fetch_all
from cartography.intel.github.util import PaginatedGraphqlData
from cartography.models.github.dependencies import GitHubDependencySchema
from cartography.models.github.manifests import DependencyGraphManifestSchema
from cartography.models.github.orgs import GitHubOrganizationSchema
from cartography.models.github.python_requirements import PythonLibrarySchema
from cartography.models.github.repos import GitHubBranchSchema
from cartography.models.github.repos import GitHubRepositoryCollaboratorSchema
from cartography.models.github.repos import GitHubRepositoryOwnerUserSchema
from cartography.models.github.repos import GitHubRepositorySchema
from cartography.models.github.repos import ProgrammingLanguageSchema
from cartography.util import backoff_handler
from cartography.util import retries_with_backoff
from cartography.util import timeit

logger = logging.getLogger(__name__)


# Representation of a user's permission level and affiliation to a GitHub repo. See:
# - Permission: https://docs.github.com/en/graphql/reference/enums#repositorypermission
# - Affiliation: https://docs.github.com/en/graphql/reference/enums#collaboratoraffiliation
UserAffiliationAndRepoPermission = namedtuple(
    "UserAffiliationAndRepoPermission",
    [
        "user",  # Dict
        "permission",  # 'WRITE', 'MAINTAIN', 'ADMIN', etc
        "affiliation",  # 'OUTSIDE', 'DIRECT'
    ],
)


GITHUB_ORG_REPOS_PAGINATED_GRAPHQL = """
    query($login: String!, $cursor: String, $count: Int!) {
    organization(login: $login)
        {
            url
            login
            repositories(first: $count, after: $cursor){
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
                    dependencyGraphManifests(first: 20) {
                        nodes {
                            blobPath
                            dependencies(first: 100) {
                                nodes {
                                    packageName
                                    requirements
                                    packageManager
                                }
                            }
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
        repo_name = repo["name"]
        repo_url = repo["url"]

        # Guard against None when collaborator fields are not accessible due to permissions.
        direct_info = repo.get("directCollaborators")
        outside_info = repo.get("outsideCollaborators")

        if affiliation == "OUTSIDE":
            total_outside = 0 if not outside_info else outside_info.get("totalCount", 0)
            if total_outside == 0:
                # No outside collaborators or not permitted to view; skip API calls for this repo.
                result[repo_url] = []
                continue
        else:  # DIRECT
            total_direct = 0 if not direct_info else direct_info.get("totalCount", 0)
            if total_direct == 0:
                # No direct collaborators or not permitted to view; skip API calls for this repo.
                result[repo_url] = []
                continue

        logger.info(f"Loading {affiliation} collaborators for repo {repo_name}.")
        collaborators = _get_repo_collaborators(
            token,
            api_url,
            org,
            repo_name,
            affiliation,
        )

        # nodes and edges are expected to always be present given that we only call for them if totalCount is > 0
        # however sometimes GitHub returns None, as in issue 1334 and 1404.
        for collab in collaborators.nodes or []:
            collab_users.append(collab)

        # The `or []` is because `.edges` can be None.
        for perm in collaborators.edges or []:
            collab_permission.append(perm["permission"])

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
    logger.info(
        f'Retrieving repo collaborators for affiliation "{affiliation}" on org "{org}".',
    )
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
    token: str,
    api_url: str,
    organization: str,
    repo: str,
    affiliation: str,
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
        "repository",
        resource_inner_type="collaborators",
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
        "repositories",
        count=50,
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
    mapping, Python requirements files (if any) in a repo, manifests from GitHub's dependency graph, and all
    dependencies from GitHub's dependency graph.
    """
    logger.info(f"Processing {len(repos_json)} GitHub repositories")
    transformed_repo_list: List[Dict] = []
    transformed_branches: List[Dict] = []
    transformed_repo_languages: List[Dict] = []
    owner_organizations: dict[str, Dict[str, Any]] = {}
    owner_users: dict[str, Dict[str, Any]] = {}
    collaborators_by_user: dict[str, Dict[str, Any]] = {}
    transformed_requirements_files: List[Dict] = []
    transformed_dependencies: List[Dict] = []
    transformed_manifests: List[Dict] = []
    for repo_object in repos_json:
        repo_record, branch_record = _transform_repo_objects(repo_object)

        owner_info = repo_object.get("owner", {})
        owner_type = owner_info.get("__typename")
        owner_url = owner_info.get("url")
        owner_login = owner_info.get("login")
        owner_name = owner_info.get("name")
        owner_email = owner_info.get("email")
        owner_company = owner_info.get("company")

        if owner_type == "Organization" and owner_url:
            owner_organizations[owner_url] = {
                "id": owner_url,
                "login": owner_login,
            }
            repo_record["owner_org_id"] = owner_url
        elif owner_type == "User" and owner_url:
            owner_users.setdefault(
                owner_url,
                {
                    "id": owner_url,
                    "login": owner_login,
                    "name": owner_name,
                    "email": owner_email,
                    "company": owner_company,
                },
            )
            repo_record["owner_user_id"] = owner_url

        transformed_repo_list.append(repo_record)
        if branch_record:
            transformed_branches.append(branch_record)

        _transform_repo_languages(
            repo_record["id"],
            repo_object,
            transformed_repo_languages,
        )

        repo_url = repo_record["id"]
        if repo_url in outside_collaborators:
            _transform_collaborators(
                repo_url,
                outside_collaborators[repo_url],
                collaborators_by_user,
            )
        if repo_url in direct_collaborators:
            _transform_collaborators(
                repo_url,
                direct_collaborators[repo_url],
                collaborators_by_user,
            )

        _transform_requirements_txt(
            repo_object["requirements"],
            repo_url,
            transformed_requirements_files,
        )
        _transform_setup_cfg_requirements(
            repo_object["setupCfg"],
            repo_url,
            transformed_requirements_files,
        )
        _transform_dependency_manifests(
            repo_object.get("dependencyGraphManifests"),
            repo_url,
            transformed_manifests,
        )
        _transform_dependency_graph(
            repo_object.get("dependencyGraphManifests"),
            repo_url,
            transformed_dependencies,
        )

    collaborators: List[Dict[str, Any]] = []
    for user_url, collaborator_data in collaborators_by_user.items():
        formatted_entry: Dict[str, Any] = {"id": user_url}
        for key, value in collaborator_data.items():
            if key == "id":
                continue
            if isinstance(value, set):
                formatted_entry[key] = sorted(value)
            else:
                formatted_entry[key] = value

        owner_entry = owner_users.get(user_url)
        if owner_entry:
            for metadata_key in ("login", "name", "email", "company"):
                metadata_value = formatted_entry.get(metadata_key)
                if metadata_value:
                    owner_entry[metadata_key] = metadata_value
        else:
            owner_users[user_url] = {
                "id": user_url,
                "login": formatted_entry.get("login"),
                "name": formatted_entry.get("name"),
                "email": formatted_entry.get("email"),
                "company": formatted_entry.get("company"),
            }

        collaborators.append(formatted_entry)

    results = {
        "repos": transformed_repo_list,
        "branches": transformed_branches,
        "repo_languages": transformed_repo_languages,
        "owner_organizations": list(owner_organizations.values()),
        "owner_users": list(owner_users.values()),
        "collaborators": collaborators,
        "python_requirements": transformed_requirements_files,
        "dependencies": transformed_dependencies,
        "manifests": transformed_manifests,
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
    Convert SSH URL to git:// URL.
    Example:
        git@github.com:cartography-cncf/cartography.git
        -> git://github.com/cartography-cncf/cartography.git
    """
    # Remove the user part (e.g., "git@")
    _, host_and_path = ssh_url.split("@", 1)
    # Replace first ':' (separating host and repo) with '/'
    host, path = host_and_path.split(":", 1)
    return f"git://{host}/{path}"


def _transform_repo_objects(input_repo_object: Dict) -> tuple[Dict, Optional[Dict]]:
    """
    Performs data transforms including creating necessary IDs for unique nodes in the graph related to GitHub repos
    and their default branches.
    :param input_repo_object: A repository node from GitHub; see tests.data.github.repos.GET_REPOS for data shape.
    :return: Tuple of the transformed repo object and an optional default branch object.
    """
    dbr = input_repo_object["defaultBranchRef"]
    default_branch_name = dbr["name"] if dbr else None
    default_branch_id = (
        _create_default_branch_id(input_repo_object["url"], dbr["id"]) if dbr else None
    )

    ssh_url = input_repo_object.get("sshUrl")
    git_url = _create_git_url_from_ssh_url(ssh_url) if ssh_url else None

    primary_language = input_repo_object.get("primaryLanguage")
    primary_language_name = primary_language["name"] if primary_language else None

    repo_record = {
        "id": input_repo_object["url"],
        "createdat": input_repo_object["createdAt"],
        "name": input_repo_object["name"],
        "fullname": input_repo_object["nameWithOwner"],
        "description": input_repo_object["description"],
        "primarylanguage": primary_language_name,
        "homepage": input_repo_object["homepageUrl"],
        "defaultbranch": default_branch_name,
        "defaultbranchid": default_branch_id,
        "private": input_repo_object["isPrivate"],
        "disabled": input_repo_object["isDisabled"],
        "archived": input_repo_object["isArchived"],
        "locked": input_repo_object["isLocked"],
        "giturl": git_url,
        "url": input_repo_object["url"],
        "sshurl": ssh_url,
        "updatedat": input_repo_object["updatedAt"],
        "owner_org_id": None,
        "owner_user_id": None,
    }

    branch_record: Optional[Dict[str, Any]] = None
    if default_branch_id and default_branch_name:
        branch_record = {
            "id": default_branch_id,
            "name": default_branch_name,
            "repo_id": input_repo_object["url"],
        }

    return repo_record, branch_record


def _transform_repo_languages(
    repo_url: str,
    repo: Dict,
    repo_languages: List[Dict],
) -> None:
    """
    Helper function to transform the languages in a GitHub repo.
    :param repo_url: The URL of the repo.
    :param repo: The repo object; see tests.data.github.repos.GET_REPOS for data shape.
    :param repo_languages: Output array to append transformed results to.
    :return: Nothing.
    """
    if repo["languages"]["totalCount"] > 0:
        for language in repo["languages"]["nodes"]:
            language_name = language["name"]
            repo_languages.append(
                {
                    "id": language_name,
                    "name": language_name,
                    "repo_id": repo_url,
                },
            )


def _transform_collaborators(
    repo_url: str,
    collaborators: List[UserAffiliationAndRepoPermission],
    collaborators_by_user: Dict[str, Dict[str, Any]],
) -> None:
    """
    Aggregate collaborator information by user so it can be loaded via the data model.
    :param collaborators: For data shape, see
        cartography.tests.data.github.repos.DIRECT_COLLABORATORS
        cartography.tests.data.github.repos.OUTSIDE_COLLABORATORS
    :param repo_url: The URL of the GitHub repo.
    :param collaborators_by_user: Aggregated collaborator output keyed by user URL.
    :return: Nothing.
    """
    if not collaborators:
        return

    for collaborator in collaborators:
        user = collaborator.user or {}
        user_url = user.get("url")
        if not user_url:
            continue

        collaborator_entry = collaborators_by_user.setdefault(
            user_url,
            {
                "id": user_url,
                "login": user.get("login"),
                "name": user.get("name"),
                "email": user.get("email"),
                "company": user.get("company"),
            },
        )

        for metadata_key in ("login", "name", "email", "company"):
            value = user.get(metadata_key)
            if value:
                collaborator_entry[metadata_key] = value

        relationship_field = _collaborator_relationship_field(
            collaborator.affiliation,
            collaborator.permission,
        )
        repo_ids = collaborator_entry.setdefault(relationship_field, set())
        repo_ids.add(repo_url)


def _collaborator_relationship_field(affiliation: str, permission: str) -> str:
    return f"{affiliation.lower()}_collab_{permission.lower()}_repo_ids"


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
        _transform_python_requirements(
            requirements_list,
            repo_url,
            out_requirements_files,
        )


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


def _transform_dependency_manifests(
    dependency_manifests: Optional[Dict],
    repo_url: str,
    out_manifests_list: List[Dict],
) -> None:
    """
    Transform GitHub dependency graph manifests into cartography manifest format.
    :param dependency_manifests: dependencyGraphManifests from GitHub GraphQL API
    :param repo_url: The URL of the GitHub repo
    :param out_manifests_list: Output array to append transformed results to
    :return: Nothing
    """
    if not dependency_manifests or not dependency_manifests.get("nodes"):
        return

    manifests_added = 0

    for manifest in dependency_manifests["nodes"]:
        blob_path = manifest.get("blobPath", "")
        if not blob_path:
            continue

        # Count dependencies in this manifest
        dependencies = manifest.get("dependencies", {})
        dependencies_count = len(dependencies.get("nodes", []) if dependencies else [])

        # Create unique manifest ID by combining repo URL and blob path
        manifest_id = f"{repo_url}#{blob_path}"

        # Extract filename from blob path
        filename = blob_path.split("/")[-1] if blob_path else "None"

        out_manifests_list.append(
            {
                "id": manifest_id,
                "blob_path": blob_path,
                "filename": filename,
                "dependencies_count": dependencies_count,
                "repo_url": repo_url,
            }
        )
        manifests_added += 1

    if manifests_added > 0:
        repo_name = repo_url.split("/")[-1] if repo_url else "repository"
        logger.info(f"Found {manifests_added} dependency manifests in {repo_name}")


def _transform_dependency_graph(
    dependency_manifests: Optional[Dict],
    repo_url: str,
    out_dependencies_list: List[Dict],
) -> None:
    """
    Transform GitHub dependency graph manifests into cartography dependency format.
    :param dependency_manifests: dependencyGraphManifests from GitHub GraphQL API
    :param repo_url: The URL of the GitHub repo
    :param out_dependencies_list: Output array to append transformed results to
    :return: Nothing
    """
    if not dependency_manifests or not dependency_manifests.get("nodes"):
        return

    dependencies_added = 0

    for manifest in dependency_manifests["nodes"]:
        dependencies = manifest.get("dependencies", {})
        if not dependencies or not dependencies.get("nodes"):
            continue

        manifest_path = manifest.get("blobPath", "")

        for dep in dependencies["nodes"]:
            package_name = dep.get("packageName")
            if not package_name:
                continue

            requirements = dep.get("requirements", "")
            package_manager = dep.get("packageManager", "").upper()

            # Create ecosystem-specific canonical name
            canonical_name = _canonicalize_dependency_name(
                package_name, package_manager
            )

            # Create ecosystem identifier
            ecosystem = package_manager.lower() if package_manager else "unknown"

            # Create simple dependency ID using canonical name and requirements
            # This allows the same dependency to be shared across multiple repos
            requirements_for_id = (requirements or "").strip()
            dependency_id = (
                f"{canonical_name}|{requirements_for_id}"
                if requirements_for_id
                else canonical_name
            )

            # Normalize requirements field (prefer None over empty string)
            normalized_requirements = requirements if requirements else None

            # Create manifest ID for the HAS_DEP relationship
            manifest_id = f"{repo_url}#{manifest_path}"

            out_dependencies_list.append(
                {
                    "id": dependency_id,
                    "name": canonical_name,
                    "original_name": package_name,  # Keep original for reference
                    "requirements": normalized_requirements,
                    "ecosystem": ecosystem,
                    "package_manager": package_manager,
                    "manifest_path": manifest_path,
                    "manifest_id": manifest_id,
                    "repo_url": repo_url,
                    "manifest_file": (
                        manifest_path.split("/")[-1] if manifest_path else ""
                    ),
                }
            )
            dependencies_added += 1

    if dependencies_added > 0:
        repo_name = repo_url.split("/")[-1] if repo_url else "repository"
        logger.info(f"Found {dependencies_added} dependencies in {repo_name}")


def _canonicalize_dependency_name(name: str, package_manager: Optional[str]) -> str:
    """
    Canonicalize dependency names based on ecosystem conventions.
    """
    if not name:
        return name

    # For Python packages, use existing canonicalization
    if package_manager in ["PIP", "CONDA"]:
        try:
            from packaging.utils import canonicalize_name

            return str(canonicalize_name(name))
        except ImportError:
            # Fallback if packaging not available
            return name.lower().replace("_", "-")

    # For other ecosystems, use lowercase
    return name.lower()


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
        requirement_id = (
            f"{canon_name}|{pinned_version}" if pinned_version else canon_name
        )

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
    reqs.extend(
        _parse_setup_cfg_requirements(
            config.get("options", "install_requires", fallback=""),
        ),
    )
    reqs.extend(
        _parse_setup_cfg_requirements(
            config.get("options", "setup_requires", fallback=""),
        ),
    )
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
def load_github_repos(
    neo4j_session: neo4j.Session,
    update_tag: int,
    repo_data: List[Dict],
    org_url: str,
) -> None:
    load_data(
        neo4j_session,
        GitHubRepositorySchema(),
        repo_data,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def load_github_branches(
    neo4j_session: neo4j.Session,
    update_tag: int,
    branch_data: List[Dict],
) -> None:
    if not branch_data:
        return

    load_data(
        neo4j_session,
        GitHubBranchSchema(),
        branch_data,
        lastupdated=update_tag,
    )


@timeit
def load_github_languages(
    neo4j_session: neo4j.Session,
    update_tag: int,
    repo_languages: List[Dict],
) -> None:
    if not repo_languages:
        return

    load_data(
        neo4j_session,
        ProgrammingLanguageSchema(),
        repo_languages,
        lastupdated=update_tag,
    )


@timeit
def load_owner_organizations(
    neo4j_session: neo4j.Session,
    update_tag: int,
    organizations: List[Dict],
) -> None:
    if not organizations:
        return

    load_data(
        neo4j_session,
        GitHubOrganizationSchema(),
        organizations,
        lastupdated=update_tag,
    )


@timeit
def load_owner_users(
    neo4j_session: neo4j.Session,
    update_tag: int,
    users: List[Dict],
) -> None:
    if not users:
        return

    load_data(
        neo4j_session,
        GitHubRepositoryOwnerUserSchema(),
        users,
        lastupdated=update_tag,
    )


@timeit
def load_collaborators(
    neo4j_session: neo4j.Session,
    update_tag: int,
    collaborators: List[Dict],
) -> None:
    if not collaborators:
        return

    load_data(
        neo4j_session,
        GitHubRepositoryCollaboratorSchema(),
        collaborators,
        lastupdated=update_tag,
    )


@timeit
def load_python_requirements(
    neo4j_session: neo4j.Session,
    update_tag: int,
    requirements_objects: List[Dict],
) -> None:
    if not requirements_objects:
        return

    load_data(
        neo4j_session,
        PythonLibrarySchema(),
        requirements_objects,
        lastupdated=update_tag,
    )


@timeit
def load_github_dependencies(
    neo4j_session: neo4j.Session,
    update_tag: int,
    dependencies: List[Dict],
) -> None:
    """
    Ingest GitHub dependency data into Neo4j using the new data model
    :param neo4j_session: Neo4J session object for server communication
    :param update_tag: Timestamp used to determine data freshness
    :param dependencies: List of dependency objects from GitHub's dependency graph
    :return: Nothing
    """
    # Group dependencies by both repo_url and manifest_id for schema-based loading
    dependencies_by_repo_and_manifest = defaultdict(list)

    for dep in dependencies:
        repo_url = dep["repo_url"]
        manifest_id = dep["manifest_id"]
        # Create a key combining both repo_url and manifest_id
        group_key = (repo_url, manifest_id)
        # Remove repo_url and manifest_id from the dependency object since we'll pass them as kwargs
        dep_without_kwargs = {
            k: v for k, v in dep.items() if k not in ["repo_url", "manifest_id"]
        }
        dependencies_by_repo_and_manifest[group_key].append(dep_without_kwargs)

    # Load dependencies for each repository/manifest combination separately
    for (
        repo_url,
        manifest_id,
    ), group_dependencies in dependencies_by_repo_and_manifest.items():
        load_data(
            neo4j_session,
            GitHubDependencySchema(),
            group_dependencies,
            lastupdated=update_tag,
            repo_url=repo_url,
            manifest_id=manifest_id,
        )


@timeit
def load_github_dependency_manifests(
    neo4j_session: neo4j.Session,
    update_tag: int,
    manifests: List[Dict],
) -> None:
    """
    Ingest GitHub dependency manifests into Neo4j
    """
    manifests_by_repo = defaultdict(list)

    for manifest in manifests:
        repo_url = manifest["repo_url"]
        manifests_by_repo[repo_url].append(manifest)

    # Load manifests for each repository separately
    for repo_url, repo_manifests in manifests_by_repo.items():
        load_data(
            neo4j_session,
            DependencyGraphManifestSchema(),
            repo_manifests,
            lastupdated=update_tag,
            repo_url=repo_url,
        )


@timeit
def cleanup_github_dependencies(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
    repo_urls: List[str],
) -> None:
    # Run cleanup for each repository separately
    for repo_url in repo_urls:
        cleanup_params = {**common_job_parameters, "repo_url": repo_url}
        GraphJob.from_node_schema(GitHubDependencySchema(), cleanup_params).run(
            neo4j_session
        )


@timeit
def cleanup_github_manifests(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
    repo_urls: List[str],
) -> None:
    """
    Delete GitHub dependency manifests and their relationships from the graph if they were not updated in the last sync.
    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters containing UPDATE_TAG
    :param repo_urls: List of repository URLs to clean up manifests for
    """
    # Run cleanup for each repository separately
    for repo_url in repo_urls:
        cleanup_params = {**common_job_parameters, "repo_url": repo_url}
        GraphJob.from_node_schema(DependencyGraphManifestSchema(), cleanup_params).run(
            neo4j_session
        )


@timeit
def cleanup_python_requirements(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
    repo_urls: List[str],
) -> None:
    for repo_url in repo_urls:
        cleanup_params = {**common_job_parameters, "repo_url": repo_url}
        GraphJob.from_node_schema(PythonLibrarySchema(), cleanup_params).run(
            neo4j_session
        )


@timeit
def cleanup_github_repositories(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
    org_url: str,
) -> None:
    cleanup_params = {**common_job_parameters, "org_url": org_url}
    GraphJob.from_node_schema(GitHubRepositorySchema(), cleanup_params).run(
        neo4j_session
    )


@timeit
def cleanup_github_branches(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    GraphJob.from_node_schema(GitHubBranchSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_github_languages(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    GraphJob.from_node_schema(ProgrammingLanguageSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_github_collaborators(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        GitHubRepositoryCollaboratorSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def load(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
    repo_data: Dict,
    org_url: str,
) -> None:
    update_tag = common_job_parameters["UPDATE_TAG"]

    load_owner_organizations(
        neo4j_session,
        update_tag,
        repo_data["owner_organizations"],
    )
    load_owner_users(
        neo4j_session,
        update_tag,
        repo_data["owner_users"],
    )
    load_github_repos(
        neo4j_session,
        update_tag,
        repo_data["repos"],
        org_url,
    )
    load_github_branches(
        neo4j_session,
        update_tag,
        repo_data["branches"],
    )
    load_github_languages(
        neo4j_session,
        update_tag,
        repo_data["repo_languages"],
    )
    load_collaborators(
        neo4j_session,
        update_tag,
        repo_data["collaborators"],
    )
    load_python_requirements(
        neo4j_session,
        update_tag,
        repo_data["python_requirements"],
    )
    load_github_dependency_manifests(
        neo4j_session,
        update_tag,
        repo_data["manifests"],
    )
    load_github_dependencies(
        neo4j_session,
        update_tag,
        repo_data["dependencies"],
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
            repos_json,
            "DIRECT",
            organization,
            github_url,
            github_api_key,
        )
        outside_collabs = _get_repo_collaborators_for_multiple_repos(
            repos_json,
            "OUTSIDE",
            organization,
            github_url,
            github_api_key,
        )
    except TypeError:
        # due to permission errors or transient network error or some other nonsense
        logger.warning(
            "Unable to list repo collaborators due to permission errors; continuing on.",
            exc_info=True,
        )
    repo_data = transform(repos_json, direct_collabs, outside_collabs)
    org_url = f"https://github.com/{organization}"
    load(neo4j_session, common_job_parameters, repo_data, org_url)

    # Collect repository URLs that have dependencies for cleanup
    repo_urls_with_dependencies = list(
        {dep["repo_url"] for dep in repo_data["dependencies"]}
    )
    cleanup_github_dependencies(
        neo4j_session, common_job_parameters, repo_urls_with_dependencies
    )

    # Collect repository URLs that have manifests for cleanup
    repo_urls_with_manifests = list(
        {manifest["repo_url"] for manifest in repo_data["manifests"]}
    )
    cleanup_github_manifests(
        neo4j_session, common_job_parameters, repo_urls_with_manifests
    )

    repo_urls_with_requirements = list(
        {req["repo_url"] for req in repo_data["python_requirements"]}
    )
    cleanup_python_requirements(
        neo4j_session, common_job_parameters, repo_urls_with_requirements
    )

    cleanup_github_repositories(
        neo4j_session, common_job_parameters, org_url
    )
    cleanup_github_branches(neo4j_session, common_job_parameters)
    cleanup_github_languages(neo4j_session, common_job_parameters)
    cleanup_github_collaborators(neo4j_session, common_job_parameters)
