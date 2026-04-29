"""Integration tests for GitLab CI config + includes."""

from unittest.mock import patch

from cartography.intel.gitlab.ci_config import sync_gitlab_ci_config
from cartography.intel.gitlab.ci_variables import load_project_variables
from cartography.intel.gitlab.ci_variables import transform_variables
from tests.data.gitlab.ci_configs import LINT_RESPONSE
from tests.data.gitlab.ci_configs import TEST_GITLAB_URL
from tests.data.gitlab.ci_configs import TEST_PROJECT_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = 10


def _create_project(neo4j_session):
    neo4j_session.run(
        """
        MERGE (p:GitLabProject{id: $project_id, gitlab_url: $gitlab_url})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $update_tag, p.default_branch = 'main'
        """,
        project_id=TEST_PROJECT_ID,
        gitlab_url=TEST_GITLAB_URL,
        update_tag=TEST_UPDATE_TAG,
    )


def _common_job_parameters():
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORGANIZATION_ID": TEST_ORG_ID,
        "org_id": TEST_ORG_ID,
        "gitlab_url": TEST_GITLAB_URL,
    }


def _project_variables_raw():
    return [
        {
            "key": "DATABASE_URL",
            "value": "ignore-me",
            "variable_type": "env_var",
            "protected": True,
            "masked": True,
            "environment_scope": "production",
        },
        {
            "key": "DEPLOY_TOKEN",
            "value": "ignore-me",
            "variable_type": "env_var",
            "protected": True,
            "masked": True,
            "environment_scope": "*",
        },
        {
            "key": "UNUSED",
            "value": "ignore-me",
            "variable_type": "env_var",
            "protected": False,
            "masked": False,
            "environment_scope": "*",
        },
    ]


@patch("cartography.intel.gitlab.ci_config.make_request_with_retry")
def test_sync_ci_config_creates_config_includes_and_variable_links(
    mock_make_request, neo4j_session
):
    """End-to-end: project + variables + ci/lint -> CIConfig + includes + REFERENCES_VARIABLE."""
    _create_project(neo4j_session)

    # Pre-load project variables.
    project_variables = transform_variables(
        _project_variables_raw(),
        "project",
        TEST_PROJECT_ID,
        TEST_GITLAB_URL,
    )
    load_project_variables(
        neo4j_session,
        project_variables,
        TEST_PROJECT_ID,
        TEST_GITLAB_URL,
        TEST_UPDATE_TAG,
    )

    # Mock the HTTP call to /ci/lint so it returns our fixture.
    class _FakeResponse:
        def __init__(self, json_body):
            self._json = json_body
            self.status_code = 200
            self.text = ""

        def json(self):
            return self._json

        def raise_for_status(self):
            return None

    mock_make_request.return_value = _FakeResponse(LINT_RESPONSE)

    sync_gitlab_ci_config(
        neo4j_session,
        TEST_GITLAB_URL,
        "fake-token",
        TEST_UPDATE_TAG,
        _common_job_parameters(),
        projects=[{"id": TEST_PROJECT_ID, "default_branch": "main"}],
        variables_by_project={TEST_PROJECT_ID: project_variables},
    )

    # Exactly one CIConfig.
    configs = check_nodes(
        neo4j_session,
        "GitLabCIConfig",
        ["id", "is_merged", "is_valid", "has_includes"],
    )
    assert configs == {(f"{TEST_PROJECT_ID}:.gitlab-ci.yml", True, True, True)}

    # Includes — at least one pinned and one unpinned project include.
    include_pinning = check_nodes(
        neo4j_session,
        "GitLabCIInclude",
        ["include_type", "is_pinned"],
    )
    assert ("project", True) in include_pinning
    assert ("project", False) in include_pinning

    # USES_INCLUDE relationship exists between config and includes.
    uses_rels = check_rels(
        neo4j_session,
        "GitLabCIConfig",
        "id",
        "GitLabCIInclude",
        "id",
        "USES_INCLUDE",
    )
    assert len(uses_rels) >= 4  # local + 2 project + remote + template

    # REFERENCES_VARIABLE matchlink — DATABASE_URL and DEPLOY_TOKEN.
    var_rels = check_rels(
        neo4j_session,
        "GitLabCIConfig",
        "id",
        "GitLabCIVariable",
        "key",
        "REFERENCES_VARIABLE",
    )
    assert {key for _, key in var_rels} == {"DATABASE_URL", "DEPLOY_TOKEN"}

    # HAS_CI_CONFIG project relationship.
    config_rels = check_rels(
        neo4j_session,
        "GitLabProject",
        "id",
        "GitLabCIConfig",
        "id",
        "HAS_CI_CONFIG",
    )
    assert config_rels == {(TEST_PROJECT_ID, f"{TEST_PROJECT_ID}:.gitlab-ci.yml")}
