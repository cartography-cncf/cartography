import copy
from unittest.mock import patch

import pytest

import cartography.intel.ontology.packages
import cartography.intel.semgrep.dependencies
import cartography.intel.semgrep.deployment
import tests.data.semgrep.dependencies
import tests.data.semgrep.deployment
from cartography.intel.semgrep.dependencies import parse_and_validate_semgrep_ecosystems
from cartography.intel.semgrep.dependencies import sync_dependencies
from cartography.intel.semgrep.deployment import sync_deployment
from tests.integration.cartography.intel.semgrep.common import create_github_repos
from tests.integration.cartography.intel.semgrep.common import create_gitlab_projects
from tests.integration.cartography.intel.semgrep.common import (
    TEST_GITLAB_PROJECT_WEB_URL,
)
from tests.integration.cartography.intel.semgrep.common import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def test_parse_and_validate_semgrep_ecosystems():
    expected_format = "gomod,npm"
    assert parse_and_validate_semgrep_ecosystems(expected_format) == ["gomod", "npm"]

    acceptable_format = "Gomod, NPM"
    assert parse_and_validate_semgrep_ecosystems(acceptable_format) == ["gomod", "npm"]

    bad_delimiter = "gomod;npm"
    with pytest.raises(ValueError):
        parse_and_validate_semgrep_ecosystems(bad_delimiter)

    ecosystem_that_does_not_exist = "gomod,npm,doesnotexist"
    with pytest.raises(ValueError):
        parse_and_validate_semgrep_ecosystems(ecosystem_that_does_not_exist)

    absolute_garbage = "#@$@#RDFFHKjsdfkjsd,KDFJHW#@,"
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
    sync_deployment(
        neo4j_session,
        semgrep_app_token,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    sync_dependencies(
        neo4j_session,
        semgrep_app_token,
        ecosystems,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

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
        "SemgrepGoLibrary",
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
        "SemgrepNpmLibrary",
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
            "simpsoncorp/sample_repo",
            "github.com/foo/baz|1.2.3",
        ),
        (
            "simpsoncorp/sample_repo",
            "github.com/foo/buzz|4.5.0",
        ),
        (
            "simpsoncorp/sample_repo",
            "github.com/foo/biz|5.0.0",
        ),
    }


_GITLAB_GOMOD_URL = (
    f"{TEST_GITLAB_PROJECT_WEB_URL}/-/blob/"
    "00000000000000000000000000000000/go.mod#L6"
)
_GITLAB_NPM_URL = (
    f"{TEST_GITLAB_PROJECT_WEB_URL}/-/blob/"
    "00000000000000000000000000000000/package-lock.json#L7"
)


def _build_gitlab_gomod_deps():
    deps = copy.deepcopy(tests.data.semgrep.dependencies.RAW_DEPS_GOMOD)
    for dep in deps:
        dep["definedAt"]["url"] = _GITLAB_GOMOD_URL
    return deps


def _build_gitlab_npm_deps():
    deps = copy.deepcopy(tests.data.semgrep.dependencies.RAW_DEPS_NPM)
    for dep in deps:
        dep["definedAt"]["url"] = _GITLAB_NPM_URL
    return deps


def _mock_get_gitlab_dependencies(
    semgrep_app_token: str, deployment_id: str, ecosystem: str
):
    if ecosystem == "gomod":
        return _build_gitlab_gomod_deps()
    if ecosystem == "npm":
        return _build_gitlab_npm_deps()
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
def test_sync_dependencies_promotes_sca_finding_to_package_ontology(
    mock_get_dependencies, mock_get_deployment, neo4j_session
):
    """
    A SemgrepSCAFinding that AFFECTS a SemgrepDependency should reach the
    canonical Package ontology node once the packages ontology sync runs:
    the dependency dedups into a :Package via DETECTED_AS, and the finding's
    AFFECTS edge is propagated onto that :Package.
    """
    # Arrange: real dependency nodes (carrying normalized_id) + a SCA finding
    # that affects one of them.
    create_github_repos(neo4j_session)
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}
    sync_deployment(
        neo4j_session,
        "your_semgrep_app_token",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    sync_dependencies(
        neo4j_session,
        "your_semgrep_app_token",
        "gomod,npm",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    neo4j_session.run(
        """
        MATCH (d:SemgrepDependency {id: 'github.com/foo/baz|1.2.3'})
        MERGE (f:SemgrepSCAFinding:SecurityIssue {id: 'test-sca-finding'})
        MERGE (f)-[:AFFECTS]->(d)
        """,
    )

    # Act
    cartography.intel.ontology.packages.sync(
        neo4j_session,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert: the dependency deduped into a canonical Package...
    detected = neo4j_session.run(
        """
        MATCH (p:Package)-[:DETECTED_AS]->(:SemgrepDependency {id: 'github.com/foo/baz|1.2.3'})
        RETURN count(p) AS c
        """,
    ).single()
    assert detected["c"] == 1

    # ...and the finding's AFFECTS edge reached that canonical Package.
    affects = neo4j_session.run(
        """
        MATCH (:SemgrepSCAFinding {id: 'test-sca-finding'})-[:AFFECTS]->(p:Package)
              -[:DETECTED_AS]->(:SemgrepDependency {id: 'github.com/foo/baz|1.2.3'})
        RETURN count(p) AS c
        """,
    ).single()
    assert affects["c"] == 1


@patch.object(
    cartography.intel.semgrep.deployment,
    "get_deployment",
    return_value=tests.data.semgrep.deployment.DEPLOYMENTS,
)
@patch.object(
    cartography.intel.semgrep.dependencies,
    "get_dependencies",
    side_effect=_mock_get_gitlab_dependencies,
)
def test_sync_dependencies_links_gitlab_project(
    mock_get_dependencies, mock_get_deployment, neo4j_session
):
    # Arrange
    create_gitlab_projects(neo4j_session)
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    # Act
    sync_deployment(
        neo4j_session,
        "your_semgrep_app_token",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    sync_dependencies(
        neo4j_session,
        "your_semgrep_app_token",
        "gomod,npm",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert GitLab REQUIRES edges for every dependency.
    assert check_rels(
        neo4j_session,
        "GitLabProject",
        "web_url",
        "SemgrepDependency",
        "id",
        "REQUIRES",
    ) == {
        (TEST_GITLAB_PROJECT_WEB_URL, "github.com/foo/baz|1.2.3"),
        (TEST_GITLAB_PROJECT_WEB_URL, "github.com/foo/buzz|4.5.0"),
        (TEST_GITLAB_PROJECT_WEB_URL, "github.com/foo/biz|5.0.0"),
    }
