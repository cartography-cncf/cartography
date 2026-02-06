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


def _ensure_repo_exists(neo4j_session):
    """Ensure the GitHubOrganization and GitHubRepository nodes exist for sync tests."""
    neo4j_session.run(
        """
        MERGE (org:GitHubOrganization{id: "https://github.com/simpsoncorp"})
        SET org.username = "simpsoncorp"

        MERGE (repo:GitHubRepository{id: "https://github.com/simpsoncorp/sample_repo"})
        SET repo.name = "sample_repo"

        MERGE (repo)-[:OWNER]->(org)
        """,
    )


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
def test_sync_github_actions_org_secrets(
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
    """Test that organization-level secrets are synced correctly."""
    # Arrange
    _ensure_repo_exists(neo4j_session)

    # Act
    cartography.intel.github.actions.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    # Assert - Verify org-level secrets were created with correct properties
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
        (
            "https://github.com/simpsoncorp/sample_repo/actions/secrets/DEPLOY_KEY",
            "DEPLOY_KEY",
            "repository",
            None,
        ),
        (
            "https://github.com/simpsoncorp/sample_repo/actions/secrets/DATABASE_URL",
            "DATABASE_URL",
            "repository",
            None,
        ),
        (
            "https://github.com/simpsoncorp/sample_repo/environments/production/secrets/PROD_API_KEY",
            "PROD_API_KEY",
            "environment",
            None,
        ),
        (
            "https://github.com/simpsoncorp/sample_repo/environments/staging/secrets/STAGING_API_KEY",
            "STAGING_API_KEY",
            "environment",
            None,
        ),
    }

    # Assert - Verify org secrets RESOURCE relationship to organization
    org_secret_rels = check_rels(
        neo4j_session,
        "GitHubActionsSecret",
        "id",
        "GitHubOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    )
    assert {
        (
            "https://github.com/simpsoncorp/actions/secrets/NPM_TOKEN",
            "https://github.com/simpsoncorp",
        ),
        (
            "https://github.com/simpsoncorp/actions/secrets/AWS_ACCESS_KEY_ID",
            "https://github.com/simpsoncorp",
        ),
    }.issubset(org_secret_rels)


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
def test_sync_github_actions_org_variables(
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
    """Test that organization-level variables are synced correctly."""
    # Arrange
    _ensure_repo_exists(neo4j_session)

    # Act
    cartography.intel.github.actions.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    # Assert - Verify org-level variables were created
    expected_org_variables = {
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
    actual_variables = check_nodes(
        neo4j_session, "GitHubActionsVariable", ["id", "name", "value", "level"]
    )
    assert expected_org_variables.issubset(actual_variables)


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
def test_sync_github_actions_workflows(
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
    """Test that repository workflows are synced correctly."""
    # Arrange
    _ensure_repo_exists(neo4j_session)

    # Act
    cartography.intel.github.actions.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    # Assert - Verify workflow nodes were created
    assert check_nodes(
        neo4j_session, "GitHubWorkflow", ["id", "name", "path", "state"]
    ) == {
        (12345678, "CI", ".github/workflows/ci.yml", "active"),
        (12345679, "Deploy", ".github/workflows/deploy.yml", "active"),
        (12345680, "Stale Check", ".github/workflows/stale.yml", "disabled_manually"),
    }

    # Assert - Verify HAS_WORKFLOW relationships to repository
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

    # Assert - Verify RESOURCE relationships to organization
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
def test_sync_github_actions_environments(
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
    """Test that repository environments are synced correctly."""
    # Arrange
    _ensure_repo_exists(neo4j_session)

    # Act
    cartography.intel.github.actions.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    # Assert - Verify environment nodes were created
    assert check_nodes(neo4j_session, "GitHubEnvironment", ["id", "name"]) == {
        (987654321, "production"),
        (987654322, "staging"),
    }

    # Assert - Verify HAS_ENVIRONMENT relationships to repository
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

    # Assert - Verify RESOURCE relationships to organization
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
def test_sync_github_actions_repo_secrets(
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
    """Test that repository-level secrets are synced correctly."""
    # Arrange
    _ensure_repo_exists(neo4j_session)

    # Act
    cartography.intel.github.actions.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    # Assert - Verify repo-level secrets were created
    expected_repo_secrets = {
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
    actual_secrets = check_nodes(
        neo4j_session, "GitHubActionsSecret", ["id", "name", "level"]
    )
    assert expected_repo_secrets.issubset(actual_secrets)

    # Assert - Verify HAS_SECRET relationships to repository
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
def test_sync_github_actions_repo_variables(
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
    """Test that repository-level variables are synced correctly."""
    # Arrange
    _ensure_repo_exists(neo4j_session)

    # Act
    cartography.intel.github.actions.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    # Assert - Verify repo-level variables were created
    expected_repo_variables = {
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
    actual_variables = check_nodes(
        neo4j_session, "GitHubActionsVariable", ["id", "name", "value", "level"]
    )
    assert expected_repo_variables.issubset(actual_variables)


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
def test_sync_github_actions_env_secrets(
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
    """Test that environment-level secrets are synced correctly."""
    # Arrange
    _ensure_repo_exists(neo4j_session)

    # Act
    cartography.intel.github.actions.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    # Assert - Verify environment-level secrets were created
    expected_env_secrets = {
        (
            "https://github.com/simpsoncorp/sample_repo/environments/production/secrets/PROD_API_KEY",
            "PROD_API_KEY",
            "environment",
        ),
        (
            "https://github.com/simpsoncorp/sample_repo/environments/staging/secrets/STAGING_API_KEY",
            "STAGING_API_KEY",
            "environment",
        ),
    }
    actual_secrets = check_nodes(
        neo4j_session, "GitHubActionsSecret", ["id", "name", "level"]
    )
    assert expected_env_secrets.issubset(actual_secrets)

    # Assert - Verify HAS_SECRET relationships to environments
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
        (
            "https://github.com/simpsoncorp/sample_repo/environments/staging/secrets/STAGING_API_KEY",
            987654322,
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
def test_sync_github_actions_env_variables(
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
    """Test that environment-level variables are synced correctly."""
    # Arrange
    _ensure_repo_exists(neo4j_session)

    # Act
    cartography.intel.github.actions.sync(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
    )

    # Assert - Verify environment-level variables were created
    expected_env_variables = {
        (
            "https://github.com/simpsoncorp/sample_repo/environments/production/variables/API_URL",
            "API_URL",
            "https://api.production.example.com",
            "environment",
        ),
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
    actual_variables = check_nodes(
        neo4j_session, "GitHubActionsVariable", ["id", "name", "value", "level"]
    )
    assert expected_env_variables.issubset(actual_variables)

    # Assert - Verify HAS_VARIABLE relationships to environments
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
            "https://github.com/simpsoncorp/sample_repo/environments/production/variables/API_URL",
            987654321,
        ),
        (
            "https://github.com/simpsoncorp/sample_repo/environments/staging/variables/API_URL",
            987654322,
        ),
        (
            "https://github.com/simpsoncorp/sample_repo/environments/staging/variables/DEBUG_MODE",
            987654322,
        ),
    }
