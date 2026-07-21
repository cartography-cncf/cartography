"""
GitHub Actions intel module for syncing Workflows, Secrets, Variables, and Environments.

Supports three levels:
- Organization-level: secrets/variables shared across repos
- Repository-level: secrets/variables specific to a repo
- Environment-level: secrets/variables specific to a deployment environment
"""

import logging
import threading
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from urllib.parse import quote

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.client.core.tx import run_write_query
from cartography.graph.job import GraphJob
from cartography.intel.github.util import _get_rest_api_base_url
from cartography.intel.github.util import fetch_all_rest_api_pages
from cartography.intel.github.util import get_file_content
from cartography.intel.github.workflow_parser import deduplicate_actions
from cartography.intel.github.workflow_parser import parse_workflow_yaml
from cartography.intel.github.workflow_parser import ParsedWorkflow
from cartography.models.github.action import GitHubActionSchema
from cartography.models.github.actions_secret import GitHubEnvActionsSecretSchema
from cartography.models.github.actions_secret import GitHubOrgActionsSecretSchema
from cartography.models.github.actions_secret import GitHubRepoActionsSecretSchema
from cartography.models.github.actions_variable import GitHubEnvActionsVariableSchema
from cartography.models.github.actions_variable import GitHubOrgActionsVariableSchema
from cartography.models.github.actions_variable import GitHubRepoActionsVariableSchema
from cartography.models.github.environment import GitHubEnvironmentSchema
from cartography.models.github.workflow import GitHubWorkflowSchema
from cartography.util import run_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


# =============================================================================
# Fetch Functions
# =============================================================================


@timeit
def get_org_secrets(
    token: str,
    api_url: str,
    organization: str,
) -> list[dict[str, Any]]:
    """
    Fetch organization-level Actions secrets.
    GET /orgs/{org}/actions/secrets
    """
    base_url = _get_rest_api_base_url(api_url)
    endpoint = f"/orgs/{organization}/actions/secrets"
    return fetch_all_rest_api_pages(token, base_url, endpoint, "secrets")


@timeit
def get_org_variables(
    token: str,
    api_url: str,
    organization: str,
) -> list[dict[str, Any]]:
    """
    Fetch organization-level Actions variables.
    GET /orgs/{org}/actions/variables
    """
    base_url = _get_rest_api_base_url(api_url)
    endpoint = f"/orgs/{organization}/actions/variables"
    return fetch_all_rest_api_pages(token, base_url, endpoint, "variables")


@timeit
def get_repo_workflows(
    token: str,
    api_url: str,
    organization: str,
    repo_name: str,
) -> list[dict[str, Any]]:
    """
    Fetch repository workflows.
    GET /repos/{owner}/{repo}/actions/workflows
    """
    base_url = _get_rest_api_base_url(api_url)
    endpoint = f"/repos/{organization}/{repo_name}/actions/workflows"
    return fetch_all_rest_api_pages(token, base_url, endpoint, "workflows")


@timeit
def get_repo_environments(
    token: str,
    api_url: str,
    organization: str,
    repo_name: str,
) -> list[dict[str, Any]]:
    """
    Fetch repository deployment environments.
    GET /repos/{owner}/{repo}/environments
    """
    base_url = _get_rest_api_base_url(api_url)
    endpoint = f"/repos/{organization}/{repo_name}/environments"
    return fetch_all_rest_api_pages(token, base_url, endpoint, "environments")


@timeit
def get_repo_secrets(
    token: str,
    api_url: str,
    organization: str,
    repo_name: str,
) -> list[dict[str, Any]]:
    """
    Fetch repository-level Actions secrets.
    GET /repos/{owner}/{repo}/actions/secrets
    """
    base_url = _get_rest_api_base_url(api_url)
    endpoint = f"/repos/{organization}/{repo_name}/actions/secrets"
    return fetch_all_rest_api_pages(token, base_url, endpoint, "secrets")


@timeit
def get_repo_variables(
    token: str,
    api_url: str,
    organization: str,
    repo_name: str,
) -> list[dict[str, Any]]:
    """
    Fetch repository-level Actions variables.
    GET /repos/{owner}/{repo}/actions/variables
    """
    base_url = _get_rest_api_base_url(api_url)
    endpoint = f"/repos/{organization}/{repo_name}/actions/variables"
    return fetch_all_rest_api_pages(token, base_url, endpoint, "variables")


@timeit
def get_env_secrets(
    token: str,
    api_url: str,
    organization: str,
    repo_name: str,
    env_name: str,
) -> list[dict[str, Any]]:
    """
    Fetch environment-level Actions secrets.
    GET /repos/{owner}/{repo}/environments/{environment_name}/secrets
    """
    base_url = _get_rest_api_base_url(api_url)
    # Environment names may contain special characters, so URL-encode them
    encoded_env = quote(env_name, safe="")
    endpoint = f"/repos/{organization}/{repo_name}/environments/{encoded_env}/secrets"
    return fetch_all_rest_api_pages(token, base_url, endpoint, "secrets")


@timeit
def get_env_variables(
    token: str,
    api_url: str,
    organization: str,
    repo_name: str,
    env_name: str,
) -> list[dict[str, Any]]:
    """
    Fetch environment-level Actions variables.
    GET /repos/{owner}/{repo}/environments/{environment_name}/variables
    """
    base_url = _get_rest_api_base_url(api_url)
    # Environment names may contain special characters, so URL-encode them
    encoded_env = quote(env_name, safe="")
    endpoint = f"/repos/{organization}/{repo_name}/environments/{encoded_env}/variables"
    return fetch_all_rest_api_pages(token, base_url, endpoint, "variables")


# =============================================================================
# Transform Functions
# =============================================================================


def transform_org_secrets(
    secrets: list[dict[str, Any]],
    organization: str,
) -> list[dict[str, Any]]:
    """
    Transform organization-level secrets, adding computed fields.
    """
    org_url = f"https://github.com/{organization}"
    result = []
    for secret in secrets:
        result.append(
            {
                **secret,
                "id": f"https://github.com/{organization}/actions/secrets/{secret['name']}",
                "level": "organization",
                "org_url": org_url,
            }
        )
    return result


def transform_org_variables(
    variables: list[dict[str, Any]],
    organization: str,
) -> list[dict[str, Any]]:
    """
    Transform organization-level variables, adding computed fields.
    """
    org_url = f"https://github.com/{organization}"
    result = []
    for var in variables:
        result.append(
            {
                **var,
                "id": f"https://github.com/{organization}/actions/variables/{var['name']}",
                "level": "organization",
                "org_url": org_url,
            }
        )
    return result


def transform_workflows(
    workflows: list[dict[str, Any]],
    organization: str,
    repo_name: str,
) -> list[dict[str, Any]]:
    """
    Transform workflows, adding computed fields.
    """
    repo_url = f"https://github.com/{organization}/{repo_name}"
    result = []
    for wf in workflows:
        result.append(
            {
                **wf,
                "repo_url": repo_url,
            }
        )
    return result


def transform_environments(
    environments: list[dict[str, Any]],
    organization: str,
    repo_name: str,
) -> list[dict[str, Any]]:
    """
    Transform environments, adding computed fields.
    """
    repo_url = f"https://github.com/{organization}/{repo_name}"
    result = []
    for env in environments:
        result.append(
            {
                **env,
                "repo_url": repo_url,
            }
        )
    return result


def transform_repo_secrets(
    secrets: list[dict[str, Any]],
    organization: str,
    repo_name: str,
) -> list[dict[str, Any]]:
    """
    Transform repository-level secrets, adding computed fields.
    """
    repo_url = f"https://github.com/{organization}/{repo_name}"
    result = []
    for secret in secrets:
        result.append(
            {
                **secret,
                "id": f"https://github.com/{organization}/{repo_name}/actions/secrets/{secret['name']}",
                "level": "repository",
                "repo_url": repo_url,
                # repo-level secrets don't have visibility
                "visibility": None,
            }
        )
    return result


def transform_repo_variables(
    variables: list[dict[str, Any]],
    organization: str,
    repo_name: str,
) -> list[dict[str, Any]]:
    """
    Transform repository-level variables, adding computed fields.
    """
    repo_url = f"https://github.com/{organization}/{repo_name}"
    result = []
    for var in variables:
        result.append(
            {
                **var,
                "id": f"https://github.com/{organization}/{repo_name}/actions/variables/{var['name']}",
                "level": "repository",
                "repo_url": repo_url,
                # repo-level variables don't have visibility
                "visibility": None,
            }
        )
    return result


def transform_env_secrets(
    secrets: list[dict[str, Any]],
    organization: str,
    repo_name: str,
    env_name: str,
    env_id: int,
) -> list[dict[str, Any]]:
    """
    Transform environment-level secrets, adding computed fields.
    """
    result = []
    for secret in secrets:
        result.append(
            {
                **secret,
                "id": f"https://github.com/{organization}/{repo_name}/environments/{env_name}/secrets/{secret['name']}",
                "level": "environment",
                "env_id": env_id,
                # env-level secrets don't have visibility
                "visibility": None,
            }
        )
    return result


def transform_env_variables(
    variables: list[dict[str, Any]],
    organization: str,
    repo_name: str,
    env_name: str,
    env_id: int,
) -> list[dict[str, Any]]:
    """
    Transform environment-level variables, adding computed fields.
    """
    result = []
    for var in variables:
        result.append(
            {
                **var,
                "id": f"https://github.com/{organization}/{repo_name}/environments/{env_name}/variables/{var['name']}",
                "level": "environment",
                "env_id": env_id,
                # env-level variables don't have visibility
                "visibility": None,
            }
        )
    return result


# =============================================================================
# Workflow Content Fetching and Parsing
# =============================================================================


@timeit
def get_workflow_content(
    token: str,
    api_url: str,
    organization: str,
    repo_name: str,
    workflow_path: str,
) -> str | None:
    """
    Fetch the content of a workflow file from GitHub.

    :param token: The GitHub API token
    :param api_url: The GitHub API URL
    :param organization: The organization name
    :param repo_name: The repository name
    :param workflow_path: The path to the workflow file (e.g., .github/workflows/ci.yml)
    :return: The workflow file content, or None if fetching fails
    """
    base_url = _get_rest_api_base_url(api_url)
    return get_file_content(
        token, organization, repo_name, workflow_path, base_url=base_url
    )


def enrich_workflow_with_parsed_content(
    workflow: dict[str, Any],
    parsed: ParsedWorkflow | None,
    organization: str,
    repo_name: str,
) -> dict[str, Any]:
    """
    Enrich a workflow dict with parsed content from the YAML file.

    :param workflow: The workflow dict from transform_workflows
    :param parsed: The parsed workflow content, or None if parsing failed
    :param organization: The organization name
    :param repo_name: The repository name
    :return: Enriched workflow dict with parsed fields
    """
    if parsed is None:
        return {
            **workflow,
            "trigger_events": None,
            "permissions_actions": None,
            "permissions_contents": None,
            "permissions_packages": None,
            "permissions_pull_requests": None,
            "permissions_issues": None,
            "permissions_deployments": None,
            "permissions_statuses": None,
            "permissions_checks": None,
            "permissions_id_token": None,
            "permissions_security_events": None,
            "env_vars": None,
            "job_count": None,
            "has_reusable_workflow_calls": None,
            "secret_ids": [],
        }

    # Build secret IDs for both org-level and repo-level secrets
    # The relationship will only be created if the secret exists
    secret_ids = []
    for secret_name in parsed.secret_refs:
        # Add repo-level secret ID
        secret_ids.append(
            f"https://github.com/{organization}/{repo_name}/actions/secrets/{secret_name}"
        )
        # Add org-level secret ID
        secret_ids.append(
            f"https://github.com/{organization}/actions/secrets/{secret_name}"
        )

    return {
        **workflow,
        "trigger_events": parsed.trigger_events if parsed.trigger_events else None,
        "permissions_actions": parsed.permissions.get("actions"),
        "permissions_contents": parsed.permissions.get("contents"),
        "permissions_packages": parsed.permissions.get("packages"),
        "permissions_pull_requests": parsed.permissions.get("pull_requests"),
        "permissions_issues": parsed.permissions.get("issues"),
        "permissions_deployments": parsed.permissions.get("deployments"),
        "permissions_statuses": parsed.permissions.get("statuses"),
        "permissions_checks": parsed.permissions.get("checks"),
        "permissions_id_token": parsed.permissions.get("id_token"),
        "permissions_security_events": parsed.permissions.get("security_events"),
        "env_vars": list(parsed.env_vars) if parsed.env_vars else None,
        "job_count": parsed.job_count,
        "has_reusable_workflow_calls": len(parsed.reusable_workflow_calls) > 0,
        "secret_ids": secret_ids,
    }


def transform_actions(
    parsed: ParsedWorkflow,
    workflow_id: int,
    organization: str,
    repo_name: str,
) -> list[dict[str, Any]]:
    """
    Transform parsed actions into data dicts for loading.

    :param parsed: The parsed workflow content
    :param workflow_id: The workflow ID (for relationship)
    :param organization: The organization name
    :param repo_name: The repository name
    :return: List of action data dicts
    """
    actions = deduplicate_actions(parsed.actions)
    result = []

    for action in actions:
        # Local actions (e.g., ./.github/actions/build) are repo-specific,
        # so include repo_name to avoid cross-repo ID collisions.
        if action.is_local:
            action_id = f"{organization}/{repo_name}:{action.raw_uses}"
        else:
            action_id = f"{organization}:{action.raw_uses}"

        result.append(
            {
                "id": action_id,
                "owner": action.owner or None,
                "name": action.name,
                "version": action.version or None,
                "is_pinned": action.is_pinned,
                "is_local": action.is_local,
                "full_name": action.full_name,
                "workflow_id": workflow_id,
            }
        )

    return result


# =============================================================================
# Load Functions
# =============================================================================


@timeit
def load_org_secrets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
    org_url: str,
) -> None:
    load(
        neo4j_session,
        GitHubOrgActionsSecretSchema(),
        data,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def load_org_variables(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
    org_url: str,
) -> None:
    load(
        neo4j_session,
        GitHubOrgActionsVariableSchema(),
        data,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def load_workflows(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
    org_url: str,
) -> None:
    load(
        neo4j_session,
        GitHubWorkflowSchema(),
        data,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def load_environments(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
    org_url: str,
) -> None:
    load(
        neo4j_session,
        GitHubEnvironmentSchema(),
        data,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def load_repo_secrets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
    org_url: str,
) -> None:
    load(
        neo4j_session,
        GitHubRepoActionsSecretSchema(),
        data,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def load_repo_variables(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
    org_url: str,
) -> None:
    load(
        neo4j_session,
        GitHubRepoActionsVariableSchema(),
        data,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def load_env_secrets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
    org_url: str,
) -> None:
    load(
        neo4j_session,
        GitHubEnvActionsSecretSchema(),
        data,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def load_env_variables(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
    org_url: str,
) -> None:
    load(
        neo4j_session,
        GitHubEnvActionsVariableSchema(),
        data,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def load_actions(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
    org_url: str,
) -> None:
    load(
        neo4j_session,
        GitHubActionSchema(),
        data,
        lastupdated=update_tag,
        org_url=org_url,
    )


# =============================================================================
# Cleanup Functions
# =============================================================================


@timeit
def cleanup_org_level(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Clean up stale GitHub Actions nodes scoped to the organization.
    Requires org_url in common_job_parameters.

    All GitHub Actions resources (workflows, environments, secrets, variables, actions)
    use org as their sub_resource, so they are all cleaned up here. This ensures
    resources are properly cleaned up even when their parent repo/environment is deleted.
    """
    # Workflows and environments
    GraphJob.from_node_schema(GitHubWorkflowSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(GitHubEnvironmentSchema(), common_job_parameters).run(
        neo4j_session,
    )
    # Actions used in workflows
    GraphJob.from_node_schema(GitHubActionSchema(), common_job_parameters).run(
        neo4j_session,
    )
    # Org-level secrets and variables
    GraphJob.from_node_schema(
        GitHubOrgActionsSecretSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        GitHubOrgActionsVariableSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )
    # Environment-level secrets and variables
    GraphJob.from_node_schema(
        GitHubEnvActionsSecretSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        GitHubEnvActionsVariableSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )
    # Repo-level secrets and variables
    GraphJob.from_node_schema(
        GitHubRepoActionsSecretSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        GitHubRepoActionsVariableSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )


# =============================================================================
# Helper Functions
# =============================================================================


def _get_repos_from_graph(
    neo4j_session: neo4j.Session,
    organization: str,
    skip_archived_repos: bool = False,
) -> list[dict[str, Any]]:
    """
    Get repository name/url/pushedat/synced_pushedat metadata for an
    organization from the graph.

    :param skip_archived_repos: If True, exclude archived/disabled repos.
    """
    org_url = f"https://github.com/{organization}"
    query = """
    MATCH (org:GitHubOrganization {id: $org_url})<-[:OWNER]-(repo:GitHubRepository)
    WHERE NOT $skip_archived_repos OR (repo.archived = false AND repo.disabled = false)
    RETURN repo.name AS name, repo.id AS url, repo.pushedat AS pushedat,
           repo.synced_pushedat AS synced_pushedat
    ORDER BY repo.name
    """
    result: list[dict[str, Any]] = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        query,
        org_url=org_url,
        skip_archived_repos=skip_archived_repos,
    )
    return result


# =============================================================================
# Main Sync Function
# =============================================================================


@dataclass
class _RepoActionsData:
    """All fetched-and-transformed data for a single repo's Actions resources.
    Populated by _fetch_actions_for_repo() in worker threads; consumed by
    sync() on the main thread for Neo4j writes."""

    repo_name: str
    repo_url: str = ""
    pushedat: str | None = None
    workflows_skipped: bool = False
    enriched_workflows: list[dict[str, Any]] = field(default_factory=list)
    repo_actions: list[dict[str, Any]] = field(default_factory=list)
    transformed_environments: list[dict[str, Any]] = field(default_factory=list)
    transformed_repo_secrets: list[dict[str, Any]] = field(default_factory=list)
    transformed_repo_variables: list[dict[str, Any]] = field(default_factory=list)
    env_secrets: list[dict[str, Any]] = field(default_factory=list)
    env_variables: list[dict[str, Any]] = field(default_factory=list)


def _fetch_actions_for_repo(
    repo_name: str,
    organization: str,
    github_api_key: str,
    github_url: str,
    progress_counter: "list[int]",
    progress_lock: threading.Lock,
    total: int,
    repo_url: str = "",
    pushedat: str | None = None,
    synced_pushedat: str | None = None,
    skip_unchanged_repos: bool = False,
) -> _RepoActionsData:
    """
    Fetch and transform all Actions data for a single repo.
    Returns a _RepoActionsData bundle; no Neo4j writes are performed here.
    Designed to be called from worker threads via ThreadPoolExecutor.

    :param skip_unchanged_repos: If True, skip re-fetching/re-parsing workflow
        YAML content when `pushedat` matches `synced_pushedat` (written after
        the last successful repos sync). Secrets, variables, and environments
        are always fetched regardless.
    """
    data = _RepoActionsData(repo_name=repo_name, repo_url=repo_url, pushedat=pushedat)

    skip_workflows = (
        skip_unchanged_repos
        and pushedat is not None
        and synced_pushedat is not None
        and pushedat == synced_pushedat
    )

    if skip_workflows:
        data.workflows_skipped = True
    else:
        # Workflows
        workflows = get_repo_workflows(
            github_api_key, github_url, organization, repo_name
        )
        if workflows:
            transformed_workflows = transform_workflows(
                workflows, organization, repo_name
            )
            for wf in transformed_workflows:
                content = None
                workflow_path = wf.get("path")
                if workflow_path:
                    content = get_workflow_content(
                        github_api_key,
                        github_url,
                        organization,
                        repo_name,
                        workflow_path,
                    )
                parsed = parse_workflow_yaml(content) if content else None
                enriched_wf = enrich_workflow_with_parsed_content(
                    wf,
                    parsed,
                    organization,
                    repo_name,
                )
                data.enriched_workflows.append(enriched_wf)
                if parsed and wf.get("id") is not None:
                    data.repo_actions.extend(
                        transform_actions(parsed, wf["id"], organization, repo_name)
                    )

    # Environments
    environments = get_repo_environments(
        github_api_key,
        github_url,
        organization,
        repo_name,
    )
    if environments:
        data.transformed_environments = transform_environments(
            environments,
            organization,
            repo_name,
        )

    # Repo secrets and variables
    repo_secrets = get_repo_secrets(github_api_key, github_url, organization, repo_name)
    if repo_secrets:
        data.transformed_repo_secrets = transform_repo_secrets(
            repo_secrets,
            organization,
            repo_name,
        )

    repo_variables = get_repo_variables(
        github_api_key,
        github_url,
        organization,
        repo_name,
    )
    if repo_variables:
        data.transformed_repo_variables = transform_repo_variables(
            repo_variables,
            organization,
            repo_name,
        )

    # Environment-level secrets and variables
    for env in environments or []:
        env_name = env["name"]
        env_id = env["id"]

        env_s = get_env_secrets(
            github_api_key,
            github_url,
            organization,
            repo_name,
            env_name,
        )
        if env_s:
            data.env_secrets.extend(
                transform_env_secrets(env_s, organization, repo_name, env_name, env_id)
            )

        env_v = get_env_variables(
            github_api_key,
            github_url,
            organization,
            repo_name,
            env_name,
        )
        if env_v:
            data.env_variables.extend(
                transform_env_variables(
                    env_v, organization, repo_name, env_name, env_id
                )
            )

    with progress_lock:
        progress_counter[0] += 1
        done = progress_counter[0]
    if done == 1 or done % 50 == 0 or done == total:
        logger.info(
            "Actions fetch progress for org %s: %d/%d repos completed.",
            organization,
            done,
            total,
        )

    return data


def _touch_skipped_actions_workflows(
    neo4j_session: neo4j.Session,
    skipped_repo_urls: list[str],
    update_tag: int,
) -> None:
    """
    Refresh `lastupdated` on the existing GitHubWorkflow/GitHubAction nodes for
    repos whose workflow-content fetch was skipped this run (because pushedat
    was unchanged), so the end-of-run stale-tag cleanup doesn't delete them.
    """
    if not skipped_repo_urls:
        return
    run_write_query(
        neo4j_session,
        """
        UNWIND $repo_urls AS repo_url
        MATCH (:GitHubRepository {id: repo_url})-[:HAS_WORKFLOW]->(wf:GitHubWorkflow)
        SET wf.lastupdated = $update_tag
        """,
        repo_urls=skipped_repo_urls,
        update_tag=update_tag,
    )
    run_write_query(
        neo4j_session,
        """
        UNWIND $repo_urls AS repo_url
        MATCH (:GitHubRepository {id: repo_url})-[:HAS_WORKFLOW]->(:GitHubWorkflow)
              -[:USES_ACTION]->(a:GitHubAction)
        SET a.lastupdated = $update_tag
        """,
        repo_urls=skipped_repo_urls,
        update_tag=update_tag,
    )


def _update_actions_synced_bookmarks(
    neo4j_session: neo4j.Session,
    synced_bookmarks: list[dict[str, str]],
) -> None:
    """
    No-op kept for backwards compatibility. The synced_pushedat bookmark is
    now written centrally by repos.sync() after the repos fetch completes,
    so per-stage write-back is no longer needed.

    # DEPRECATED: will be removed in v1.0.0.
    """


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    github_api_key: str,
    github_url: str,
    organization: str,
    parallel_workers: int = 1,
    skip_archived_repos: bool = False,
    skip_unchanged_repos: bool = False,
) -> list[dict[str, Any]]:
    """
    Sync GitHub Actions data (workflows, secrets, variables, environments) for an organization.

    Sync order:
    1. Organization-level secrets and variables
    2. For each repo (parallel fetch, sequential load): workflows, environments,
       repo secrets/variables, env secrets/variables
    3. Cleanup stale nodes

    :param parallel_workers: Number of repos to fetch concurrently. Default 1 (sequential).
    :param skip_archived_repos: If True, skip archived/disabled repos entirely.
    :param skip_unchanged_repos: If True, skip re-fetching/re-parsing workflow
        YAML content for repos whose `pushedat` is unchanged since the last
        successful Actions sync. Secrets/variables/environments are always
        still fetched for every repo.
    :return: List of all transformed workflows (with repo_url and path) for supply chain sync.
    """
    org_url = f"https://github.com/{organization}"
    update_tag = common_job_parameters["UPDATE_TAG"]
    all_workflows: list[dict[str, Any]] = []

    # 1. Sync organization-level secrets and variables
    logger.info("Syncing GitHub Actions for organization: %s", organization)

    org_secrets = get_org_secrets(github_api_key, github_url, organization)
    if org_secrets:
        load_org_secrets(
            neo4j_session,
            transform_org_secrets(org_secrets, organization),
            update_tag,
            org_url,
        )

    org_variables = get_org_variables(github_api_key, github_url, organization)
    if org_variables:
        load_org_variables(
            neo4j_session,
            transform_org_variables(org_variables, organization),
            update_tag,
            org_url,
        )

    # 2. Get repos from graph and sync repo-level resources
    repos = _get_repos_from_graph(
        neo4j_session,
        organization,
        skip_archived_repos=skip_archived_repos,
    )
    total = len(repos)
    logger.info(
        "Syncing GitHub Actions for %d repositories in org %s (parallel_workers=%d).",
        total,
        organization,
        parallel_workers,
    )

    progress_counter: list[int] = [0]
    progress_lock = threading.Lock()

    skipped_repo_urls: list[str] = []

    # Submit all repos to a single bounded thread pool up front so idle workers
    # immediately pick up the next repo instead of waiting for a batch's
    # slowest straggler (e.g. a repo with many workflows/environments).
    with ThreadPoolExecutor(max_workers=parallel_workers) as executor:
        futures = {
            executor.submit(
                _fetch_actions_for_repo,
                repo["name"],
                organization,
                github_api_key,
                github_url,
                progress_counter,
                progress_lock,
                total,
                repo_url=repo["url"],
                pushedat=repo.get("pushedat"),
                synced_pushedat=repo.get("synced_pushedat"),
                skip_unchanged_repos=skip_unchanged_repos,
            ): repo["name"]
            for repo in repos
        }

        # Sequential load — all Neo4j writes on the main thread, applied as
        # each repo's fetch completes rather than waiting for a fixed batch.
        for f in as_completed(futures):
            d = f.result()
            if d.enriched_workflows:
                load_workflows(neo4j_session, d.enriched_workflows, update_tag, org_url)
                all_workflows.extend(d.enriched_workflows)
            if d.repo_actions:
                load_actions(neo4j_session, d.repo_actions, update_tag, org_url)
            if d.transformed_environments:
                load_environments(
                    neo4j_session,
                    d.transformed_environments,
                    update_tag,
                    org_url,
                )
            if d.transformed_repo_secrets:
                load_repo_secrets(
                    neo4j_session,
                    d.transformed_repo_secrets,
                    update_tag,
                    org_url,
                )
            if d.transformed_repo_variables:
                load_repo_variables(
                    neo4j_session,
                    d.transformed_repo_variables,
                    update_tag,
                    org_url,
                )
            if d.env_secrets:
                load_env_secrets(neo4j_session, d.env_secrets, update_tag, org_url)
            if d.env_variables:
                load_env_variables(neo4j_session, d.env_variables, update_tag, org_url)

            if skip_unchanged_repos:
                if d.workflows_skipped:
                    skipped_repo_urls.append(d.repo_url)

    if skip_unchanged_repos:
        _touch_skipped_actions_workflows(neo4j_session, skipped_repo_urls, update_tag)
        logger.info(
            "GitHub Actions incremental sync for org %s: skipped workflow refetch "
            "for %d/%d unchanged repos.",
            organization,
            len(skipped_repo_urls),
            total,
        )

    # 3. Cleanup all stale nodes scoped to the organization.
    org_cleanup_params = {**common_job_parameters, "org_url": org_url}
    # DEPRECATED: compatibility migration to backfill the RESOURCE edge from
    # GitHubOrganization to repo-level GitHubActionsSecret and
    # GitHubActionsVariable. Remove in v1.0.0.
    run_analysis_job(
        "github_repo_actions_secret_resource_edge_migration.json",
        neo4j_session,
        org_cleanup_params,
    )
    cleanup_org_level(neo4j_session, org_cleanup_params)

    return all_workflows
