from unittest.mock import patch

import cartography.intel.semgrep.deployment
import cartography.intel.semgrep.secrets
import tests.data.semgrep.deployment
import tests.data.semgrep.secrets
from cartography.intel.semgrep.deployment import sync_deployment
from cartography.intel.semgrep.secrets import sync_secrets
from tests.integration.cartography.intel.semgrep.common import create_github_repos
from tests.integration.cartography.intel.semgrep.common import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


@patch.object(
    cartography.intel.semgrep.deployment,
    "get_deployment",
    return_value=tests.data.semgrep.deployment.DEPLOYMENTS,
)
@patch.object(
    cartography.intel.semgrep.secrets,
    "get_secret_findings",
    return_value=tests.data.semgrep.secrets.RAW_SECRETS,
)
def test_sync_secrets(mock_get_secret_findings, mock_get_deployment, neo4j_session):
    # Arrange
    create_github_repos(neo4j_session)
    semgrep_app_token = "your_semgrep_app_token"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    sync_deployment(
        neo4j_session,
        semgrep_app_token,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    sync_secrets(
        neo4j_session,
        semgrep_app_token,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert nodes
    assert check_nodes(
        neo4j_session,
        "SemgrepSecretsFinding",
        [
            "id",
            "rule_hash_id",
            "repository_name",
            "ref",
            "severity",
            "confidence",
            "type",
            "validation_state",
            "status",
            "finding_path",
            "mode",
            "repository_scm_type",
            "repository_url",
        ],
    ) == {
        (
            tests.data.semgrep.secrets.SECRETS_FINDING_ID,
            "lBU41LA",
            "simpsoncorp/sample_repo",
            "main",
            "HIGH",
            "HIGH",
            "OpenAI",
            "CONFIRMED_VALID",
            "OPEN",
            "src/ai.py:232",
            "MONITOR",
            "GITHUB",
            "https://github.com/simpsoncorp/sample_repo",
        ),
    }

    # Assert deployment relationship
    assert check_rels(
        neo4j_session,
        "SemgrepDeployment",
        "id",
        "SemgrepSecretsFinding",
        "id",
        "RESOURCE",
    ) == {
        (
            "123456",
            tests.data.semgrep.secrets.SECRETS_FINDING_ID,
        ),
    }

    # Assert GitHub repo relationship
    assert check_rels(
        neo4j_session,
        "GitHubRepository",
        "fullname",
        "SemgrepSecretsFinding",
        "id",
        "FOUND_IN",
        rel_direction_right=False,
    ) == {
        (
            "simpsoncorp/sample_repo",
            tests.data.semgrep.secrets.SECRETS_FINDING_ID,
        ),
    }
