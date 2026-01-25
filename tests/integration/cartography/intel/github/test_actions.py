from unittest.mock import patch

import cartography.intel.github.actions
from tests.data.github.actions import GET_ENV_SECRETS_PRODUCTION
from tests.data.github.actions import GET_ENV_SECRETS_STAGING
from tests.data.github.actions import GET_ENV_VARIABLES_PRODUCTION
from tests.data.github.actions import GET_ENV_VARIABLES_STAGING
from tests.data.github.actions import GET_ORG_SECRETS
from tests.data.github.actions import GET_ORG_VARIABLES
from tests.data.github.actions import GET_REPO_ENVIRONMENTS
from tests.data.github.actions import GET_REPO_SECRETS
from tests.data.github.actions import GET_REPO_VARIABLES
from tests.data.github.actions import GET_REPO_WORKFLOWS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {"UPDATE_TAG": TEST_UPDATE_TAG}
TEST_GITHUB_URL = "https://fake.github.net/graphql/"
TEST_ORGANIZATION = "simpsoncorp"
FAKE_API_KEY = "asdf"


def _ensure_org_exists(neo4j_session):
    """Ensure the GitHubOrganization node exists for relationship tests."""
    neo4j_session.run(
        """
        MERGE (org:GitHubOrganization{id: "https://github.com/simpsoncorp"})
        SET org.username = "simpsoncorp"
        """,
    )


def _ensure_repo_exists(neo4j_session):
    """Ensure the GitHubRepository node exists for relationship tests."""
    neo4j_session.run(
        """
        MERGE (repo:GitHubRepository{id: "https://github.com/simpsoncorp/sample_repo"})
        SET repo.name = "sample_repo"
        """,
    )
    neo4j_session.run(
        """
        MERGE (org:GitHubOrganization{id: "https://github.com/simpsoncorp"})
        MERGE (repo:GitHubRepository{id: "https://github.com/simpsoncorp/sample_repo"})
        MERGE (repo)-[:OWNER]->(org)
        """,
    )


def test_transform_and_load_org_secrets(neo4j_session):
    """Test that we can transform and load organization-level secrets."""
    _ensure_org_exists(neo4j_session)

    transformed = cartography.intel.github.actions.transform_org_secrets(
        GET_ORG_SECRETS,
        TEST_ORGANIZATION,
    )
    cartography.intel.github.actions.load_org_secrets(
        neo4j_session,
        transformed,
        TEST_UPDATE_TAG,
        f"https://github.com/{TEST_ORGANIZATION}",
    )

    assert check_nodes(
        neo4j_session, "GitHubActionsSecret", ["id", "name", "level", "visibility"]
    ) == {
        (
            "https://github.com/simpsoncorp/actions/secrets/NPM_TOKEN",
            "NPM_TOKEN",
            "organization",
            "all",
        ),
        (
            "https://github.com/simpsoncorp/actions/secrets/AWS_ACCESS_KEY_ID",
            "AWS_ACCESS_KEY_ID",
            "organization",
            "private",
        ),
    }

    # Check relationship to organization
    assert check_rels(
        neo4j_session,
        "GitHubActionsSecret",
        "id",
        "GitHubOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (
            "https://github.com/simpsoncorp/actions/secrets/NPM_TOKEN",
            "https://github.com/simpsoncorp",
        ),
        (
            "https://github.com/simpsoncorp/actions/secrets/AWS_ACCESS_KEY_ID",
            "https://github.com/simpsoncorp",
        ),
    }


def test_transform_and_load_org_variables(neo4j_session):
    """Test that we can transform and load organization-level variables."""
    _ensure_org_exists(neo4j_session)

    transformed = cartography.intel.github.actions.transform_org_variables(
        GET_ORG_VARIABLES,
        TEST_ORGANIZATION,
    )
    cartography.intel.github.actions.load_org_variables(
        neo4j_session,
        transformed,
        TEST_UPDATE_TAG,
        f"https://github.com/{TEST_ORGANIZATION}",
    )

    assert check_nodes(
        neo4j_session, "GitHubActionsVariable", ["id", "name", "value", "level"]
    ) == {
        (
            "https://github.com/simpsoncorp/actions/variables/NODE_VERSION",
            "NODE_VERSION",
            "18",
            "organization",
        ),
        (
            "https://github.com/simpsoncorp/actions/variables/DEPLOY_ENV",
            "DEPLOY_ENV",
            "production",
            "organization",
        ),
    }


def test_transform_and_load_workflows(neo4j_session):
    """Test that we can transform and load workflows."""
    _ensure_repo_exists(neo4j_session)

    transformed = cartography.intel.github.actions.transform_workflows(
        GET_REPO_WORKFLOWS,
        TEST_ORGANIZATION,
        "sample_repo",
    )
    cartography.intel.github.actions.load_workflows(
        neo4j_session,
        transformed,
        TEST_UPDATE_TAG,
        f"https://github.com/{TEST_ORGANIZATION}",
    )

    assert check_nodes(
        neo4j_session, "GitHubWorkflow", ["id", "name", "path", "state"]
    ) == {
        (12345678, "CI", ".github/workflows/ci.yml", "active"),
        (12345679, "Deploy", ".github/workflows/deploy.yml", "active"),
        (12345680, "Stale Check", ".github/workflows/stale.yml", "disabled_manually"),
    }

    # Check relationship to repository (via other_relationships)
    assert check_rels(
        neo4j_session,
        "GitHubWorkflow",
        "id",
        "GitHubRepository",
        "id",
        "HAS_WORKFLOW",
        rel_direction_right=False,
    ) == {
        (12345678, "https://github.com/simpsoncorp/sample_repo"),
        (12345679, "https://github.com/simpsoncorp/sample_repo"),
        (12345680, "https://github.com/simpsoncorp/sample_repo"),
    }

    # Check relationship to organization (via sub_resource_relationship)
    assert check_rels(
        neo4j_session,
        "GitHubWorkflow",
        "id",
        "GitHubOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (12345678, "https://github.com/simpsoncorp"),
        (12345679, "https://github.com/simpsoncorp"),
        (12345680, "https://github.com/simpsoncorp"),
    }


def test_transform_and_load_environments(neo4j_session):
    """Test that we can transform and load environments."""
    _ensure_repo_exists(neo4j_session)

    transformed = cartography.intel.github.actions.transform_environments(
        GET_REPO_ENVIRONMENTS,
        TEST_ORGANIZATION,
        "sample_repo",
    )
    cartography.intel.github.actions.load_environments(
        neo4j_session,
        transformed,
        TEST_UPDATE_TAG,
        f"https://github.com/{TEST_ORGANIZATION}",
    )

    assert check_nodes(neo4j_session, "GitHubEnvironment", ["id", "name"]) == {
        (987654321, "production"),
        (987654322, "staging"),
    }

    # Check relationship to repository (via other_relationships)
    assert check_rels(
        neo4j_session,
        "GitHubEnvironment",
        "id",
        "GitHubRepository",
        "id",
        "HAS_ENVIRONMENT",
        rel_direction_right=False,
    ) == {
        (987654321, "https://github.com/simpsoncorp/sample_repo"),
        (987654322, "https://github.com/simpsoncorp/sample_repo"),
    }

    # Check relationship to organization (via sub_resource_relationship)
    assert check_rels(
        neo4j_session,
        "GitHubEnvironment",
        "id",
        "GitHubOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (987654321, "https://github.com/simpsoncorp"),
        (987654322, "https://github.com/simpsoncorp"),
    }


def test_transform_and_load_repo_secrets(neo4j_session):
    """Test that we can transform and load repository-level secrets."""
    _ensure_repo_exists(neo4j_session)

    transformed = cartography.intel.github.actions.transform_repo_secrets(
        GET_REPO_SECRETS,
        TEST_ORGANIZATION,
        "sample_repo",
    )
    cartography.intel.github.actions.load_repo_secrets(
        neo4j_session,
        transformed,
        TEST_UPDATE_TAG,
        "https://github.com/simpsoncorp/sample_repo",
    )

    # Query for repo-level secrets specifically
    nodes = neo4j_session.run(
        """
        MATCH (s:GitHubActionsSecret {level: "repository"})
        RETURN s.id, s.name, s.level
        """,
    )
    actual_nodes = {(n["s.id"], n["s.name"], n["s.level"]) for n in nodes}
    expected_nodes = {
        (
            "https://github.com/simpsoncorp/sample_repo/actions/secrets/DEPLOY_KEY",
            "DEPLOY_KEY",
            "repository",
        ),
        (
            "https://github.com/simpsoncorp/sample_repo/actions/secrets/DATABASE_URL",
            "DATABASE_URL",
            "repository",
        ),
    }
    assert actual_nodes == expected_nodes

    # Check relationship to repository
    assert check_rels(
        neo4j_session,
        "GitHubActionsSecret",
        "id",
        "GitHubRepository",
        "id",
        "HAS_SECRET",
        rel_direction_right=False,
    ) == {
        (
            "https://github.com/simpsoncorp/sample_repo/actions/secrets/DEPLOY_KEY",
            "https://github.com/simpsoncorp/sample_repo",
        ),
        (
            "https://github.com/simpsoncorp/sample_repo/actions/secrets/DATABASE_URL",
            "https://github.com/simpsoncorp/sample_repo",
        ),
    }


def test_transform_and_load_repo_variables(neo4j_session):
    """Test that we can transform and load repository-level variables."""
    _ensure_repo_exists(neo4j_session)

    transformed = cartography.intel.github.actions.transform_repo_variables(
        GET_REPO_VARIABLES,
        TEST_ORGANIZATION,
        "sample_repo",
    )
    cartography.intel.github.actions.load_repo_variables(
        neo4j_session,
        transformed,
        TEST_UPDATE_TAG,
        "https://github.com/simpsoncorp/sample_repo",
    )

    # Query for repo-level variables specifically
    nodes = neo4j_session.run(
        """
        MATCH (v:GitHubActionsVariable {level: "repository"})
        RETURN v.id, v.name, v.value, v.level
        """,
    )
    actual_nodes = {(n["v.id"], n["v.name"], n["v.value"], n["v.level"]) for n in nodes}
    expected_nodes = {
        (
            "https://github.com/simpsoncorp/sample_repo/actions/variables/LOG_LEVEL",
            "LOG_LEVEL",
            "info",
            "repository",
        ),
        (
            "https://github.com/simpsoncorp/sample_repo/actions/variables/MAX_RETRIES",
            "MAX_RETRIES",
            "3",
            "repository",
        ),
    }
    assert actual_nodes == expected_nodes


def test_transform_and_load_env_secrets(neo4j_session):
    """Test that we can transform and load environment-level secrets."""
    _ensure_repo_exists(neo4j_session)

    # First load the environment
    transformed_envs = cartography.intel.github.actions.transform_environments(
        GET_REPO_ENVIRONMENTS,
        TEST_ORGANIZATION,
        "sample_repo",
    )
    cartography.intel.github.actions.load_environments(
        neo4j_session,
        transformed_envs,
        TEST_UPDATE_TAG,
        f"https://github.com/{TEST_ORGANIZATION}",
    )

    # Load production environment secrets
    transformed_secrets = cartography.intel.github.actions.transform_env_secrets(
        GET_ENV_SECRETS_PRODUCTION,
        TEST_ORGANIZATION,
        "sample_repo",
        "production",
        987654321,
    )
    cartography.intel.github.actions.load_env_secrets(
        neo4j_session,
        transformed_secrets,
        TEST_UPDATE_TAG,
        f"https://github.com/{TEST_ORGANIZATION}",
    )

    # Query for env-level secrets specifically
    nodes = neo4j_session.run(
        """
        MATCH (s:GitHubActionsSecret {level: "environment"})
        RETURN s.id, s.name, s.level
        """,
    )
    actual_nodes = {(n["s.id"], n["s.name"], n["s.level"]) for n in nodes}
    expected_nodes = {
        (
            "https://github.com/simpsoncorp/sample_repo/environments/production/secrets/PROD_API_KEY",
            "PROD_API_KEY",
            "environment",
        ),
    }
    assert actual_nodes == expected_nodes

    # Check relationship to environment (via other_relationships)
    assert check_rels(
        neo4j_session,
        "GitHubActionsSecret",
        "id",
        "GitHubEnvironment",
        "id",
        "HAS_SECRET",
        rel_direction_right=False,
    ) == {
        (
            "https://github.com/simpsoncorp/sample_repo/environments/production/secrets/PROD_API_KEY",
            987654321,
        ),
    }

    # Check relationship to organization (via sub_resource_relationship)
    # Query explicitly for env-level secrets to avoid catching org-level secrets from other tests
    org_rels = neo4j_session.run(
        """
        MATCH (s:GitHubActionsSecret {level: "environment"})<-[:RESOURCE]-(o:GitHubOrganization)
        RETURN s.id, o.id
        """,
    )
    actual_org_rels = {(r["s.id"], r["o.id"]) for r in org_rels}
    assert actual_org_rels == {
        (
            "https://github.com/simpsoncorp/sample_repo/environments/production/secrets/PROD_API_KEY",
            "https://github.com/simpsoncorp",
        ),
    }


def test_transform_and_load_env_variables(neo4j_session):
    """Test that we can transform and load environment-level variables."""
    _ensure_repo_exists(neo4j_session)

    # First load the environment
    transformed_envs = cartography.intel.github.actions.transform_environments(
        GET_REPO_ENVIRONMENTS,
        TEST_ORGANIZATION,
        "sample_repo",
    )
    cartography.intel.github.actions.load_environments(
        neo4j_session,
        transformed_envs,
        TEST_UPDATE_TAG,
        f"https://github.com/{TEST_ORGANIZATION}",
    )

    # Load staging environment variables
    transformed_vars = cartography.intel.github.actions.transform_env_variables(
        GET_ENV_VARIABLES_STAGING,
        TEST_ORGANIZATION,
        "sample_repo",
        "staging",
        987654322,
    )
    cartography.intel.github.actions.load_env_variables(
        neo4j_session,
        transformed_vars,
        TEST_UPDATE_TAG,
        f"https://github.com/{TEST_ORGANIZATION}",
    )

    # Query for env-level variables specifically
    nodes = neo4j_session.run(
        """
        MATCH (v:GitHubActionsVariable {level: "environment"})
        RETURN v.id, v.name, v.value, v.level
        """,
    )
    actual_nodes = {(n["v.id"], n["v.name"], n["v.value"], n["v.level"]) for n in nodes}
    expected_nodes = {
        (
            "https://github.com/simpsoncorp/sample_repo/environments/staging/variables/API_URL",
            "API_URL",
            "https://api.staging.example.com",
            "environment",
        ),
        (
            "https://github.com/simpsoncorp/sample_repo/environments/staging/variables/DEBUG_MODE",
            "DEBUG_MODE",
            "true",
            "environment",
        ),
    }
    assert actual_nodes == expected_nodes

    # Check relationship to environment (via other_relationships)
    assert check_rels(
        neo4j_session,
        "GitHubActionsVariable",
        "id",
        "GitHubEnvironment",
        "id",
        "HAS_VARIABLE",
        rel_direction_right=False,
    ) == {
        (
            "https://github.com/simpsoncorp/sample_repo/environments/staging/variables/API_URL",
            987654322,
        ),
        (
            "https://github.com/simpsoncorp/sample_repo/environments/staging/variables/DEBUG_MODE",
            987654322,
        ),
    }

    # Check relationship to organization (via sub_resource_relationship)
    # Query explicitly for env-level variables to avoid catching org-level variables from other tests
    org_rels = neo4j_session.run(
        """
        MATCH (v:GitHubActionsVariable {level: "environment"})<-[:RESOURCE]-(o:GitHubOrganization)
        RETURN v.id, o.id
        """,
    )
    actual_org_rels = {(r["v.id"], r["o.id"]) for r in org_rels}
    assert actual_org_rels == {
        (
            "https://github.com/simpsoncorp/sample_repo/environments/staging/variables/API_URL",
            "https://github.com/simpsoncorp",
        ),
        (
            "https://github.com/simpsoncorp/sample_repo/environments/staging/variables/DEBUG_MODE",
            "https://github.com/simpsoncorp",
        ),
    }


@patch.object(
    cartography.intel.github.actions,
    "get_org_secrets",
    return_value=GET_ORG_SECRETS,
)
@patch.object(
    cartography.intel.github.actions,
    "get_org_variables",
    return_value=GET_ORG_VARIABLES,
)
@patch.object(
    cartography.intel.github.actions,
    "get_repo_workflows",
    return_value=GET_REPO_WORKFLOWS,
)
@patch.object(
    cartography.intel.github.actions,
    "get_repo_environments",
    return_value=GET_REPO_ENVIRONMENTS,
)
@patch.object(
    cartography.intel.github.actions,
    "get_repo_secrets",
    return_value=GET_REPO_SECRETS,
)
@patch.object(
    cartography.intel.github.actions,
    "get_repo_variables",
    return_value=GET_REPO_VARIABLES,
)
@patch.object(
    cartography.intel.github.actions,
    "get_env_secrets",
    side_effect=lambda *args, **kwargs: (
        GET_ENV_SECRETS_PRODUCTION
        if args[4] == "production"
        else GET_ENV_SECRETS_STAGING
    ),
)
@patch.object(
    cartography.intel.github.actions,
    "get_env_variables",
    side_effect=lambda *args, **kwargs: (
        GET_ENV_VARIABLES_PRODUCTION
        if args[4] == "production"
        else GET_ENV_VARIABLES_STAGING
    ),
)
def test_sync_github_actions(
    mock_env_variables,
    mock_env_secrets,
    mock_repo_variables,
    mock_repo_secrets,
    mock_repo_environments,
    mock_repo_workflows,
    mock_org_variables,
    mock_org_secrets,
    neo4j_session,
):
    """Test the full sync function."""
    _ensure_repo_exists(neo4j_session)

    cartography.intel.github.actions.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    # Verify workflows were created
    workflow_nodes = neo4j_session.run(
        "MATCH (w:GitHubWorkflow) RETURN count(w) as count",
    ).single()["count"]
    assert workflow_nodes == 3

    # Verify environments were created
    env_nodes = neo4j_session.run(
        "MATCH (e:GitHubEnvironment) RETURN count(e) as count",
    ).single()["count"]
    assert env_nodes == 2

    # Verify secrets were created (org + repo + env levels)
    secret_nodes = neo4j_session.run(
        "MATCH (s:GitHubActionsSecret) RETURN count(s) as count",
    ).single()["count"]
    # 2 org secrets + 2 repo secrets + 1 prod env secret + 1 staging env secret = 6
    assert secret_nodes == 6

    # Verify variables were created (org + repo + env levels)
    var_nodes = neo4j_session.run(
        "MATCH (v:GitHubActionsVariable) RETURN count(v) as count",
    ).single()["count"]
    # 2 org vars + 2 repo vars + 1 prod env var + 2 staging env vars = 7
    assert var_nodes == 7
