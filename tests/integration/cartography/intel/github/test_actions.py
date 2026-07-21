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
from tests.data.github.workflow_content import WORKFLOW_CI_CONTENT
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


def _set_repo_pushedat(neo4j_session, pushedat, synced_pushedat=None):
    neo4j_session.run(
        """
        MATCH (repo:GitHubRepository{id: "https://github.com/simpsoncorp/sample_repo"})
        SET repo.pushedat = $pushedat, repo.synced_pushedat = $synced_pushedat
        """,
        pushedat=pushedat,
        synced_pushedat=synced_pushedat,
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
@patch.object(
    cartography.intel.github.actions,
    "get_workflow_content",
    return_value=None,
)
def test_sync_github_actions_org_secrets(
    mock_workflow_content,
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
@patch.object(
    cartography.intel.github.actions,
    "get_workflow_content",
    return_value=None,
)
def test_sync_github_actions_org_variables(
    mock_workflow_content,
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
@patch.object(
    cartography.intel.github.actions,
    "get_workflow_content",
    return_value=None,
)
def test_sync_github_actions_workflows(
    mock_workflow_content,
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
@patch.object(
    cartography.intel.github.actions,
    "get_workflow_content",
    return_value=None,
)
def test_sync_github_actions_environments(
    mock_workflow_content,
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
@patch.object(
    cartography.intel.github.actions,
    "get_workflow_content",
    return_value=None,
)
def test_sync_github_actions_repo_secrets(
    mock_workflow_content,
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
@patch.object(
    cartography.intel.github.actions,
    "get_workflow_content",
    return_value=None,
)
def test_sync_github_actions_repo_variables(
    mock_workflow_content,
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
@patch.object(
    cartography.intel.github.actions,
    "get_workflow_content",
    return_value=None,
)
def test_sync_github_actions_env_secrets(
    mock_workflow_content,
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
@patch.object(
    cartography.intel.github.actions,
    "get_workflow_content",
    return_value=None,
)
def test_sync_github_actions_env_variables(
    mock_workflow_content,
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
@patch.object(
    cartography.intel.github.actions,
    "get_workflow_content",
    return_value=WORKFLOW_CI_CONTENT,
)
def test_sync_github_actions_workflow_parsing(
    mock_workflow_content,
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
    """Test that workflow YAML parsing extracts actions, secrets, and permissions."""
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

    # Assert - Verify workflows have parsed fields
    workflow = neo4j_session.run(
        "MATCH (w:GitHubWorkflow {id: 12345678}) RETURN w",
    ).single()["w"]
    assert workflow["permissions_contents"] == "read"
    assert workflow["permissions_pull_requests"] == "write"
    assert workflow["job_count"] == 2
    assert "push" in workflow["trigger_events"]

    # Assert - Verify GitHubAction nodes were created from parsed workflow content
    action_nodes = neo4j_session.run(
        "MATCH (a:GitHubAction) RETURN count(a) as count",
    ).single()["count"]
    # WORKFLOW_CI_CONTENT has 2 unique actions (checkout@v4 and setup-node@v4).
    # Action IDs are {org}:{raw_uses}, so the same action across workflows is merged.
    assert action_nodes == 2

    # Assert - Verify USES_ACTION relationships were created
    uses_action_rels = neo4j_session.run(
        "MATCH (:GitHubWorkflow)-[r:USES_ACTION]->(:GitHubAction) RETURN count(r) as count",
    ).single()["count"]
    assert uses_action_rels >= 2

    # Assert - Verify REFERENCES_SECRET relationships were created for existing secrets
    # The workflow references NPM_TOKEN which exists as an org secret
    refs_secret_rels = neo4j_session.run(
        "MATCH (:GitHubWorkflow)-[r:REFERENCES_SECRET]->(:GitHubActionsSecret) RETURN count(r) as count",
    ).single()["count"]
    assert refs_secret_rels >= 1


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
@patch.object(
    cartography.intel.github.actions,
    "get_workflow_content",
    return_value=None,
)
def test_sync_github_actions_incremental_skip_preserves_workflows(
    mock_workflow_content,
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
    """
    Test that when skip_unchanged_repos is enabled and a repo's pushedat is
    unchanged since the last successful Actions sync, the workflow fetch is
    skipped but existing GitHubWorkflow/GitHubAction nodes are preserved
    (touched, not stale-cleaned) across a new update tag.
    """
    # Arrange - repo exists, no prior pushedat/bookmark (first sync should fetch normally)
    _ensure_repo_exists(neo4j_session)
    _set_repo_pushedat(neo4j_session, pushedat="2024-01-01T00:00:00Z")

    # Act - first sync populates workflows and records the pushedat bookmark
    cartography.intel.github.actions.sync(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
        skip_unchanged_repos=True,
    )

    # Assert - first sync fetched workflows; synced_pushedat is set externally
    # (by repos.sync() in a real run) — simulate that by setting it now so the
    # second sync can use it as the bookmark.
    assert mock_repo_workflows.call_count == 1
    assert check_nodes(neo4j_session, "GitHubWorkflow", ["id"]) == {
        (12345678,),
        (12345679,),
        (12345680,),
    }
    # Simulate repos.sync() writing synced_pushedat after repos fetch
    neo4j_session.run(
        'MATCH (r:GitHubRepository{id: "https://github.com/simpsoncorp/sample_repo"}) '
        "SET r.synced_pushedat = $pushedat",
        pushedat="2024-01-01T00:00:00Z",
    )

    # Act - second sync, pushedat matches synced_pushedat, new update tag
    second_update_tag = TEST_UPDATE_TAG + 1
    cartography.intel.github.actions.sync(
        neo4j_session,
        {"UPDATE_TAG": second_update_tag},
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        TEST_ORGANIZATION,
        skip_unchanged_repos=True,
    )

    # Assert - workflow fetch was NOT called again (still just the 1 call from before)
    assert mock_repo_workflows.call_count == 1

    # Assert - GitHubWorkflow nodes still exist and were touched to the new update tag,
    # i.e. NOT deleted by stale-tag cleanup despite not being re-fetched.
    workflow_rows = neo4j_session.run(
        "MATCH (w:GitHubWorkflow) RETURN w.id AS id, w.lastupdated AS lastupdated",
    ).data()
    assert {row["id"] for row in workflow_rows} == {12345678, 12345679, 12345680}
    assert all(row["lastupdated"] == second_update_tag for row in workflow_rows)
