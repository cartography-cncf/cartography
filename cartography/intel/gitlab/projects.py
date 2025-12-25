import logging
from concurrent.futures import as_completed
from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from typing import Dict
from typing import List

import gitlab
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.common.programming_language import ProgrammingLanguageSchema
from cartography.models.gitlab.groups import GitLabGroupSchema
from cartography.models.gitlab.repositories import GitLabRepositorySchema
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Timeout for API requests in seconds
_TIMEOUT = 60


@timeit
def get_gitlab_repositories(gitlab_url: str, gitlab_token: str) -> List[Dict[str, Any]]:
    """
    Fetches repositories (projects) from the GitLab API with rich metadata.

    :param gitlab_url: URL of the GitLab instance
    :param gitlab_token: Personal access token for GitLab API authentication
    :return: A list of repository details with full metadata
    :raises ValueError: if gitlab_url or gitlab_token is not provided
    """
    if not gitlab_url or not gitlab_token:
        raise ValueError("GitLab URL and token are required")

    # Normalize URL for consistent ID generation
    normalized_url = gitlab_url.rstrip("/")

    gl = gitlab.Gitlab(url=gitlab_url, private_token=gitlab_token, timeout=_TIMEOUT)
    projects_iterator = gl.projects.list(iterator=True, all=True)

    repositories = []
    for project in projects_iterator:
        # Extract namespace information for group relationships
        namespace = project.namespace if hasattr(project, "namespace") else {}
        namespace_id = namespace.get("id") if isinstance(namespace, dict) else None

        # Create unique ID that includes GitLab instance URL for multi-instance support
        unique_id = f"{normalized_url}/projects/{project.id}"
        unique_namespace_id = (
            f"{normalized_url}/groups/{namespace_id}" if namespace_id else None
        )

        repo_data = {
            "id": unique_id,
            "numeric_id": project.id,  # Keep numeric ID for API calls
            # Core identification
            "name": project.name,
            "path": project.path,
            "path_with_namespace": project.path_with_namespace,
            # URLs
            "web_url": project.web_url,
            "http_url_to_repo": project.http_url_to_repo,
            "ssh_url_to_repo": project.ssh_url_to_repo,
            "readme_url": (
                project.readme_url if hasattr(project, "readme_url") else None
            ),
            # Metadata
            "description": project.description or "",
            "visibility": project.visibility,
            "archived": project.archived,
            "default_branch": (
                project.default_branch if hasattr(project, "default_branch") else None
            ),
            # Stats
            "star_count": project.star_count if hasattr(project, "star_count") else 0,
            "forks_count": (
                project.forks_count if hasattr(project, "forks_count") else 0
            ),
            "open_issues_count": (
                project.open_issues_count
                if hasattr(project, "open_issues_count")
                else 0
            ),
            # Timestamps
            "created_at": project.created_at,
            "last_activity_at": project.last_activity_at,
            # Features
            "issues_enabled": project.issues_enabled,
            "merge_requests_enabled": project.merge_requests_enabled,
            "wiki_enabled": project.wiki_enabled,
            "snippets_enabled": project.snippets_enabled,
            "container_registry_enabled": (
                project.container_registry_enabled
                if hasattr(project, "container_registry_enabled")
                else False
            ),
            # Access
            "empty_repo": (
                project.empty_repo if hasattr(project, "empty_repo") else False
            ),
            # For relationships (use unique IDs for multi-instance support)
            "namespace_id": unique_namespace_id,
            "namespace_numeric_id": namespace_id,  # Keep numeric ID for reference
            "namespace_kind": (
                namespace.get("kind") if isinstance(namespace, dict) else None
            ),
            "namespace_name": (
                namespace.get("name") if isinstance(namespace, dict) else None
            ),
            "namespace_path": (
                namespace.get("path") if isinstance(namespace, dict) else None
            ),
            "namespace_full_path": (
                namespace.get("full_path") if isinstance(namespace, dict) else None
            ),
        }

        repositories.append(repo_data)

    logger.info(f"Found {len(repositories)} GitLab repositories")
    return repositories


@timeit
def _extract_groups_from_repositories(
    repositories: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Extract unique groups (namespaces) from repository data.

    :param repositories: List of repository data
    :return: List of unique group data
    """
    groups_map = {}
    for repo in repositories:
        namespace_id = repo.get("namespace_id")  # This is the unique ID now
        namespace_numeric_id = repo.get("namespace_numeric_id")
        # Only process group namespaces (not user namespaces)
        if namespace_id and repo.get("namespace_kind") == "group":
            if namespace_id not in groups_map:
                groups_map[namespace_id] = {
                    "id": namespace_id,  # Unique ID with URL prefix
                    "numeric_id": namespace_numeric_id,  # Numeric ID
                    "name": repo.get("namespace_name", ""),
                    "path": repo.get("namespace_path", ""),
                    "full_path": repo.get("namespace_full_path", ""),
                    "web_url": f"{repo['web_url'].rsplit('/', 1)[0]}",  # Derive from project URL
                    "visibility": repo.get(
                        "visibility", "private"
                    ),  # Inherit from project
                    "description": "",
                }

    groups = list(groups_map.values())
    logger.info(f"Extracted {len(groups)} unique GitLab groups")
    return groups


def _fetch_languages_for_repo(
    gitlab_client: gitlab.Gitlab,
    repo_unique_id: str,
    repo_numeric_id: int,
) -> List[Dict[str, Any]]:
    """
    Fetch languages for a single repository.

    :param gitlab_client: GitLab client instance
    :param repo_unique_id: Unique repository ID (with URL prefix)
    :param repo_numeric_id: Numeric GitLab project ID for API calls
    :return: List of language mappings for this repository
    """
    try:
        project = gitlab_client.projects.get(repo_numeric_id)
        languages = project.languages()

        # languages is a dict like {"Python": 65.5, "JavaScript": 34.5}
        mappings = []
        for language_name, percentage in languages.items():
            mappings.append(
                {
                    "repo_id": repo_unique_id,
                    "language_name": language_name,
                    "percentage": percentage,
                },
            )
        return mappings
    except Exception as e:
        logger.debug(f"Could not fetch languages for project {repo_numeric_id}: {e}")
        return []


@timeit
def _get_repository_languages(
    gitlab_url: str,
    gitlab_token: str,
    repositories: List[Dict[str, Any]],
    max_workers: int = 10,
) -> List[Dict[str, Any]]:
    """
    Fetch language statistics for ALL repositories using parallel execution.

    Uses ThreadPoolExecutor to fetch language data concurrently for improved
    performance on large GitLab instances. With 10 workers, ~3000 repos should
    complete in 5-10 minutes depending on GitLab instance performance.

    :param gitlab_url: GitLab instance URL
    :param gitlab_token: API token
    :param repositories: List of repository data
    :param max_workers: Number of parallel workers (default: 10)
    :return: List of language mappings for relationships
    """
    repo_count = len(repositories)
    logger.info(
        f"Fetching languages for {repo_count} repositories using {max_workers} parallel workers",
    )

    # Create a shared GitLab client for each worker
    language_mappings = []
    completed_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a GitLab client instance per thread to avoid sharing issues
        clients = {
            i: gitlab.Gitlab(
                url=gitlab_url, private_token=gitlab_token, timeout=_TIMEOUT
            )
            for i in range(max_workers)
        }

        # Submit all repositories for language fetching
        future_to_repo: Dict[Future, Dict[str, Any]] = {}
        for repo in repositories:
            # Round-robin assign clients to futures
            client = clients[len(future_to_repo) % max_workers]
            future = executor.submit(
                _fetch_languages_for_repo,
                client,
                repo["id"],  # Unique ID with URL
                repo["numeric_id"],  # Numeric ID for API calls
            )
            future_to_repo[future] = repo

        # Process results as they complete
        for future in as_completed(future_to_repo):
            repo = future_to_repo[future]
            try:
                mappings = future.result()
                language_mappings.extend(mappings)
                completed_count += 1

                # Progress logging every 100 repos
                if completed_count % 100 == 0:
                    logger.info(
                        f"Fetched languages for {completed_count}/{repo_count} repositories...",
                    )
            except Exception as e:
                logger.warning(
                    f"Error fetching languages for repository {repo['id']}: {e}"
                )

    logger.info(
        f"Found {len(language_mappings)} language mappings from {completed_count} repositories",
    )
    return language_mappings


@timeit
def _load_gitlab_groups(
    neo4j_session: neo4j.Session,
    groups: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load GitLab group nodes into Neo4j.

    :param neo4j_session: Neo4j session
    :param groups: List of group data
    :param update_tag: Update tag for tracking data freshness
    """
    if not groups:
        logger.info("No GitLab groups to load")
        return

    logger.info(f"Loading {len(groups)} GitLab groups")
    load(
        neo4j_session,
        GitLabGroupSchema(),
        groups,
        lastupdated=update_tag,
    )


@timeit
def _load_gitlab_repositories(
    neo4j_session: neo4j.Session,
    repositories: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load GitLab repository nodes and their relationships into Neo4j.

    :param neo4j_session: Neo4j session
    :param repositories: List of repository data
    :param update_tag: Update tag for tracking data freshness
    """
    logger.info(f"Loading {len(repositories)} GitLab repositories")
    load(
        neo4j_session,
        GitLabRepositorySchema(),
        repositories,
        lastupdated=update_tag,
    )


@timeit
def _load_programming_languages(
    neo4j_session: neo4j.Session,
    language_mappings: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load programming language nodes and their relationships to repositories.

    :param neo4j_session: Neo4j session
    :param language_mappings: List of language-to-repo mappings
    :param update_tag: Update tag for tracking data freshness
    """
    if not language_mappings:
        logger.info("No language mappings to load")
        return

    logger.info(f"Loading {len(language_mappings)} language relationships")

    # Extract unique languages
    unique_languages = {}
    for mapping in language_mappings:
        lang_name = mapping["language_name"]
        if lang_name not in unique_languages:
            unique_languages[lang_name] = {"name": lang_name}

    # Load ProgrammingLanguage nodes first
    language_nodes = list(unique_languages.values())
    logger.info(f"Loading {len(language_nodes)} unique programming languages")
    load(
        neo4j_session,
        ProgrammingLanguageSchema(),
        language_nodes,
        lastupdated=update_tag,
    )

    # Create LANGUAGE relationships using raw Cypher to link existing nodes
    # NOTE: Raw Cypher is the CORRECT approach here (not legacy code).
    # Using load() with GitLabRepositorySchema would overwrite repo properties with NULL
    # since we only provide {id, language_name, percentage}. This matches the established
    # pattern for creating relationships between existing nodes without modification.
    ingest_languages_query = """
        UNWIND $LanguageMappings as mapping

        MATCH (repo:GitLabRepository {id: mapping.repo_id})
        MATCH (lang:ProgrammingLanguage {name: mapping.language_name})

        MERGE (repo)-[r:LANGUAGE]->(lang)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $UpdateTag,
            r.percentage = mapping.percentage
    """

    neo4j_session.run(
        ingest_languages_query,
        LanguageMappings=language_mappings,
        UpdateTag=update_tag,
    )


@timeit
def _cleanup_gitlab_data(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Remove stale GitLab data from Neo4j.

    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters including UPDATE_TAG
    """
    # Cleanup repositories (nodes and OWNER relationships)
    GraphJob.from_node_schema(GitLabRepositorySchema(), common_job_parameters).run(
        neo4j_session
    )
    # Cleanup groups
    GraphJob.from_node_schema(GitLabGroupSchema(), common_job_parameters).run(
        neo4j_session
    )
    # Cleanup LANGUAGE relationships (created via raw Cypher)
    # NOTE: Raw Cypher is correct here for linking existing nodes. Cleanup via JSON file is
    # the established pattern when relationships are created outside the schema load() system.
    run_cleanup_job("gitlab_repos_cleanup.json", neo4j_session, common_job_parameters)


@timeit
def sync_gitlab_repositories(
    neo4j_session: neo4j.Session,
    gitlab_url: str,
    gitlab_token: str,
    update_tag: int,
) -> None:
    """
    Synchronizes GitLab repositories data with Neo4j.

    This creates a rich graph with:
    - GitLabRepository nodes with extensive metadata
    - GitLabGroup nodes representing namespaces
    - ProgrammingLanguage nodes
    - OWNER relationships: GitLabGroup -> GitLabRepository
    - LANGUAGE relationships: GitLabRepository -> ProgrammingLanguage

    :param neo4j_session: Neo4j session
    :param gitlab_url: The GitLab instance URL
    :param gitlab_token: GitLab API access token
    :param update_tag: Update tag for tracking data freshness
    """
    # Normalize URL for consistent ID generation and cleanup scoping
    normalized_url = gitlab_url.rstrip("/")

    common_job_parameters = {
        "UPDATE_TAG": update_tag,
        "GITLAB_URL": normalized_url,  # For multi-instance cleanup scoping
    }

    logger.info("Syncing GitLab repositories")

    # Fetch repositories with rich metadata
    repositories = get_gitlab_repositories(gitlab_url, gitlab_token)

    # Extract groups from repository namespaces
    groups = _extract_groups_from_repositories(repositories)

    # Load groups first (they're referenced by repositories)
    _load_gitlab_groups(neo4j_session, groups, update_tag)

    # Load repositories and their group relationships
    _load_gitlab_repositories(neo4j_session, repositories, update_tag)

    # Fetch and load language data
    language_mappings = _get_repository_languages(
        gitlab_url, gitlab_token, repositories
    )
    _load_programming_languages(neo4j_session, language_mappings, update_tag)

    # Cleanup stale data
    _cleanup_gitlab_data(neo4j_session, common_job_parameters)

    logger.info("Finished syncing GitLab repositories")
