from unittest.mock import patch

import cartography.intel.semgrep.dependencies
import cartography.intel.semgrep.deployment
import tests.data.semgrep.dependencies
import tests.data.semgrep.deployment
from cartography.intel.semgrep.dependencies import sync_dependencies
from cartography.intel.semgrep.deployment import sync_deployment
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
    cartography.intel.semgrep.dependencies,
    "get_dependencies",
    return_value=tests.data.semgrep.dependencies.RAW_DEPS,
)
def test_sync_dependencies(mock_get_dependencies, mock_get_deployment, neo4j_session):
    # Arrange
    create_github_repos(neo4j_session)
    semgrep_app_token = "your_semgrep_app_token"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    sync_deployment(neo4j_session, semgrep_app_token, TEST_UPDATE_TAG, common_job_parameters)
    sync_dependencies(neo4j_session, semgrep_app_token, TEST_UPDATE_TAG, common_job_parameters)

    # Assert
    assert check_nodes(
        neo4j_session,
        "SemgrepDeployment",
        ["id", "name", "slug"],
    ) == {("123456", "Org", "org")}

    assert check_nodes(
        neo4j_session,
        "SemgrepDependency",
        [
            "id",
            "lastupdated",
            "name",
            "version",
            "ecosystem",
        ],
    ) == {
        (
            "github.com/foo/baz|1.2.3",
            TEST_UPDATE_TAG,
            "github.com/foo/baz",
            "1.2.3",
            "gomod",
        ),
        (
            "github.com/foo/buzz|4.5.0",
            TEST_UPDATE_TAG,
            "github.com/foo/buzz",
            "4.5.0",
            "gomod",
        ),
    }

    assert check_rels(
        neo4j_session,
        "SemgrepDeployment",
        "id",
        "SemgrepDependency",
        "id",
        "RESOURCE",
    ) == {
        (
            "123456",
            "github.com/foo/baz|1.2.3",
        ),
        (
            "123456",
            "github.com/foo/buzz|4.5.0",
        ),
    }

    assert check_rels(
        neo4j_session,
        "GitHubRepository",
        "fullname",
        "SemgrepDependency",
        "id",
        "REQUIRES",
    ) == {
        (
            "org/repository",
            "github.com/foo/baz|1.2.3",
        ),
        (
            "org/repository",
            "github.com/foo/buzz|4.5.0",
        ),
    }
