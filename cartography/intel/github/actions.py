"""
GitHub Actions intel module for syncing Workflows, Secrets, Variables, and Environments.

Supports three levels:
- Organization-level: secrets/variables shared across repos
- Repository-level: secrets/variables specific to a repo
- Environment-level: secrets/variables specific to a deployment environment
"""

import logging
from typing import Any
from urllib.parse import quote

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import read_list_of_values_tx
from cartography.graph.job import GraphJob
from cartography.intel.github.util import _get_rest_api_base_url
from cartography.intel.github.util import fetch_all_rest_api_pages
from cartography.models.github.actions_secret import GitHubEnvActionsSecretSchema
from cartography.models.github.actions_secret import GitHubOrgActionsSecretSchema
from cartography.models.github.actions_secret import GitHubRepoActionsSecretSchema
from cartography.models.github.actions_variable import GitHubEnvActionsVariableSchema
from cartography.models.github.actions_variable import GitHubOrgActionsVariableSchema
from cartography.models.github.actions_variable import GitHubRepoActionsVariableSchema
from cartography.models.github.environment import GitHubEnvironmentSchema
from cartography.models.github.workflow import GitHubWorkflowSchema
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
# Load Functions
# =============================================================================


@timeit
def load_org_secrets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
    org_url: str,
) -> None:
    logger.info(f"Loading {len(data)} GitHub organization Actions secrets to the graph")
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
    logger.info(
        f"Loading {len(data)} GitHub organization Actions variables to the graph"
    )
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
    logger.info(f"Loading {len(data)} GitHub workflows to the graph")
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
    logger.info(f"Loading {len(data)} GitHub environments to the graph")
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
    repo_url: str,
) -> None:
    logger.info(f"Loading {len(data)} GitHub repository Actions secrets to the graph")
    load(
        neo4j_session,
        GitHubRepoActionsSecretSchema(),
        data,
        lastupdated=update_tag,
        repo_url=repo_url,
    )


@timeit
def load_repo_variables(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
    repo_url: str,
) -> None:
    logger.info(f"Loading {len(data)} GitHub repository Actions variables to the graph")
    load(
        neo4j_session,
        GitHubRepoActionsVariableSchema(),
        data,
        lastupdated=update_tag,
        repo_url=repo_url,
    )


@timeit
def load_env_secrets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
    org_url: str,
) -> None:
    logger.info(f"Loading {len(data)} GitHub environment Actions secrets to the graph")
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
    logger.info(
        f"Loading {len(data)} GitHub environment Actions variables to the graph"
    )
    load(
        neo4j_session,
        GitHubEnvActionsVariableSchema(),
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

    All GitHub Actions resources (workflows, environments, secrets, variables)
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


@timeit
def cleanup_repo_level(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    repo_url: str,
) -> None:
    """
    Clean up stale repository-level GitHub Actions secrets and variables.
    """
    cleanup_params = {**common_job_parameters, "repo_url": repo_url}
    GraphJob.from_node_schema(GitHubRepoActionsSecretSchema(), cleanup_params).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(GitHubRepoActionsVariableSchema(), cleanup_params).run(
        neo4j_session,
    )


# =============================================================================
# Helper Functions
# =============================================================================


def _get_repos_from_graph(neo4j_session: neo4j.Session, organization: str) -> list[str]:
    """
    Get repository names for an organization from the graph.
    """
    org_url = f"https://github.com/{organization}"
    query = """
    MATCH (org:GitHubOrganization {id: $org_url})<-[:OWNER]-(repo:GitHubRepository)
    RETURN repo.name
    ORDER BY repo.name
    """
    result: list[str] = neo4j_session.execute_read(
        read_list_of_values_tx,
        query,
        org_url=org_url,
    )
    return result


# =============================================================================
# Main Sync Function
# =============================================================================


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    github_api_key: str,
    github_url: str,
    organization: str,
) -> None:
    """
    Sync GitHub Actions data (workflows, secrets, variables, environments) for an organization.

    Sync order:
    1. Organization-level secrets and variables
    2. For each repo: workflows, environments, repo secrets/variables
    3. For each environment: env secrets/variables
    4. Cleanup stale nodes
    """
    org_url = f"https://github.com/{organization}"
    update_tag = common_job_parameters["UPDATE_TAG"]

    # 1. Sync organization-level secrets and variables
    logger.info(f"Syncing GitHub Actions for organization: {organization}")

    org_secrets = get_org_secrets(github_api_key, github_url, organization)
    if org_secrets:
        transformed_org_secrets = transform_org_secrets(org_secrets, organization)
        load_org_secrets(neo4j_session, transformed_org_secrets, update_tag, org_url)

    org_variables = get_org_variables(github_api_key, github_url, organization)
    if org_variables:
        transformed_org_variables = transform_org_variables(org_variables, organization)
        load_org_variables(
            neo4j_session, transformed_org_variables, update_tag, org_url
        )

    # 2. Get repos from graph and sync repo-level resources
    repo_names = _get_repos_from_graph(neo4j_session, organization)
    logger.info(f"Syncing GitHub Actions for {len(repo_names)} repositories")

    for repo_name in repo_names:
        repo_url = f"https://github.com/{organization}/{repo_name}"

        # Sync workflows
        workflows = get_repo_workflows(
            github_api_key, github_url, organization, repo_name
        )
        if workflows:
            transformed_workflows = transform_workflows(
                workflows, organization, repo_name
            )
            load_workflows(neo4j_session, transformed_workflows, update_tag, org_url)

        # Sync environments (must come before env secrets/variables)
        environments = get_repo_environments(
            github_api_key, github_url, organization, repo_name
        )
        if environments:
            transformed_environments = transform_environments(
                environments, organization, repo_name
            )
            load_environments(
                neo4j_session, transformed_environments, update_tag, org_url
            )

        # Sync repo-level secrets
        repo_secrets = get_repo_secrets(
            github_api_key, github_url, organization, repo_name
        )
        if repo_secrets:
            transformed_repo_secrets = transform_repo_secrets(
                repo_secrets, organization, repo_name
            )
            load_repo_secrets(
                neo4j_session, transformed_repo_secrets, update_tag, repo_url
            )

        # Sync repo-level variables
        repo_variables = get_repo_variables(
            github_api_key, github_url, organization, repo_name
        )
        if repo_variables:
            transformed_repo_variables = transform_repo_variables(
                repo_variables, organization, repo_name
            )
            load_repo_variables(
                neo4j_session, transformed_repo_variables, update_tag, repo_url
            )

        # 3. Sync environment-level secrets and variables
        for env in environments or []:
            env_name = env["name"]
            env_id = env["id"]

            env_secrets = get_env_secrets(
                github_api_key, github_url, organization, repo_name, env_name
            )
            if env_secrets:
                transformed_env_secrets = transform_env_secrets(
                    env_secrets,
                    organization,
                    repo_name,
                    env_name,
                    env_id,
                )
                load_env_secrets(
                    neo4j_session, transformed_env_secrets, update_tag, org_url
                )

            env_variables = get_env_variables(
                github_api_key, github_url, organization, repo_name, env_name
            )
            if env_variables:
                transformed_env_variables = transform_env_variables(
                    env_variables,
                    organization,
                    repo_name,
                    env_name,
                    env_id,
                )
                load_env_variables(
                    neo4j_session, transformed_env_variables, update_tag, org_url
                )

        # Cleanup repo-level resources for this repo
        cleanup_repo_level(neo4j_session, common_job_parameters, repo_url)

    # 4. Cleanup org-level stale nodes
    org_cleanup_params = {**common_job_parameters, "org_url": org_url}
    cleanup_org_level(neo4j_session, org_cleanup_params)
