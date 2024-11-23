from unittest.mock import patch

import pytest

import cartography.intel.semgrep.dependencies
import cartography.intel.semgrep.deployment
import tests.data.semgrep.dependencies
import tests.data.semgrep.deployment
from cartography.intel.semgrep.dependencies import parse_and_validate_semgrep_ecosystems
from cartography.intel.semgrep.dependencies import sync_dependencies
from cartography.intel.semgrep.deployment import sync_deployment
from tests.integration.cartography.intel.semgrep.common import create_github_repos
from tests.integration.cartography.intel.semgrep.common import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def test_parse_and_validate_semgrep_ecosystems():
    expected_format = "gomod,npm"
    assert parse_and_validate_semgrep_ecosystems(expected_format) == ['gomod', 'npm']

    acceptable_format = "Gomod, NPM"
    assert parse_and_validate_semgrep_ecosystems(acceptable_format) == ['gomod', 'npm']

    bad_delimiter = "gomod;npm"
    with pytest.raises(ValueError):
        parse_and_validate_semgrep_ecosystems(bad_delimiter)

    ecosystem_that_does_not_exist = "gomod,npm,doesnotexist"
    with pytest.raises(ValueError):
        parse_and_validate_semgrep_ecosystems(ecosystem_that_does_not_exist)

    absolute_garbage = '#@$@#RDFFHKjsdfkjsd,KDFJHW#@,'
    with pytest.raises(ValueError):
        parse_and_validate_semgrep_ecosystems(absolute_garbage)


def _mock_get_dependencies(semgrep_app_token: str, deployment_id: str, ecosystem: str):
    if ecosystem == "gomod":
        return tests.data.semgrep.dependencies.RAW_DEPS_GOMOD
    elif ecosystem == "npm":
        return tests.data.semgrep.dependencies.RAW_DEPS_NPM
    else:
        raise ValueError(f"Unexpected value for `ecosystem`: {ecosystem}")


@patch.object(
    cartography.intel.semgrep.deployment,
    "get_deployment",
    return_value=tests.data.semgrep.deployment.DEPLOYMENTS,
)
@patch.object(
    cartography.intel.semgrep.dependencies,
    "get_dependencies",
    side_effect=_mock_get_dependencies,
)
def test_sync_dependencies(mock_get_dependencies, mock_get_deployment, neo4j_session):
    # Arrange
    create_github_repos(neo4j_session)
    semgrep_app_token = "your_semgrep_app_token"
    ecosystems = "gomod,npm"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    sync_deployment(neo4j_session, semgrep_app_token, TEST_UPDATE_TAG, common_job_parameters)
    sync_dependencies(neo4j_session, semgrep_app_token, ecosystems, TEST_UPDATE_TAG, common_job_parameters)

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
        (
            "github.com/foo/biz|5.0.0",
            TEST_UPDATE_TAG,
            "github.com/foo/biz",
            "5.0.0",
            "npm",
        ),
    }

    assert check_nodes(
        neo4j_session,
        "GoLibrary",
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

    assert check_nodes(
        neo4j_session,
        "NpmLibrary",
        [
            "id",
            "lastupdated",
            "name",
            "version",
            "ecosystem",
        ],
    ) == {
        (
            "github.com/foo/biz|5.0.0",
            TEST_UPDATE_TAG,
            "github.com/foo/biz",
            "5.0.0",
            "npm",
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
        (
            "123456",
            "github.com/foo/biz|5.0.0",
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
        (
            "org/repository",
            "github.com/foo/biz|5.0.0",
        ),
    }
