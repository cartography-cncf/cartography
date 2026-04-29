"""Integration tests for GitLab CI config + includes."""

from unittest.mock import Mock

import requests

from cartography.intel.gitlab.ci_config import sync_gitlab_ci_config
from cartography.intel.gitlab.ci_variables import load_project_variables
from cartography.intel.gitlab.ci_variables import transform_variables
from tests.data.gitlab.ci_configs import LINT_RESPONSE
from tests.data.gitlab.ci_configs import PIPELINE_WITH_MIXED_INCLUDES
from tests.data.gitlab.ci_configs import TEST_GITLAB_URL
from tests.data.gitlab.ci_configs import TEST_PROJECT_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = 10


def _reset_db_and_create_project(neo4j_session):
    """Wipe shared session state and create a fresh project node."""
    neo4j_session.run("MATCH (n) DETACH DELETE n;")
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


def _make_response(status_code, *, json_body=None, text_body=""):
    """Build a Mock that mimics a `requests.Response` for our needs."""
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    response.headers = {}
    response.text = text_body
    response.json.return_value = json_body or {}
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=response
        )
    else:
        response.raise_for_status.return_value = None
    return response


def _patch_lint_then_raw(monkeypatch, lint_response, raw_yaml):
    """
    Patch `requests.request` (the actual HTTP boundary used by
    `make_request_with_retry`) to dispatch on URL: ``/ci/lint`` returns the
    given lint response, the raw-file endpoint returns the raw YAML.
    """

    def fake_request(method, url, **_kwargs):
        if "/ci/lint" in url:
            return lint_response
        if "/repository/files/" in url:
            return _make_response(200, text_body=raw_yaml)
        return _make_response(404)

    monkeypatch.setattr("cartography.intel.gitlab.util.requests.request", fake_request)
    monkeypatch.setattr("cartography.intel.gitlab.util.time.sleep", lambda _: None)


def _load_variables(neo4j_session):
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
    return project_variables


def test_sync_ci_config_uses_lint_path_when_available(neo4j_session, monkeypatch):
    """When /ci/lint returns a merged YAML, that path is used (is_merged=True)."""
    _reset_db_and_create_project(neo4j_session)
    project_variables = _load_variables(neo4j_session)

    lint_response = _make_response(200, json_body=LINT_RESPONSE)
    _patch_lint_then_raw(monkeypatch, lint_response, raw_yaml="")

    sync_gitlab_ci_config(
        neo4j_session,
        TEST_GITLAB_URL,
        "fake-token",
        TEST_UPDATE_TAG,
        _common_job_parameters(),
        projects=[{"id": TEST_PROJECT_ID, "default_branch": "main"}],
        variables_by_project={TEST_PROJECT_ID: project_variables},
    )

    configs = check_nodes(
        neo4j_session,
        "GitLabCIConfig",
        ["id", "is_merged", "is_valid"],
    )
    assert configs == {(f"{TEST_PROJECT_ID}:.gitlab-ci.yml", True, True)}

    # Variables referenced by the merged pipeline (DATABASE_URL, DEPLOY_TOKEN).
    var_rels = check_rels(
        neo4j_session,
        "GitLabCIConfig",
        "id",
        "GitLabCIVariable",
        "key",
        "REFERENCES_VARIABLE",
    )
    assert {key for _, key in var_rels} == {"DATABASE_URL", "DEPLOY_TOKEN"}


def test_sync_ci_config_falls_back_to_raw_when_lint_denied(neo4j_session, monkeypatch):
    """403 on /ci/lint must fall back to the raw .gitlab-ci.yml endpoint."""
    _reset_db_and_create_project(neo4j_session)
    project_variables = _load_variables(neo4j_session)

    _patch_lint_then_raw(
        monkeypatch,
        lint_response=_make_response(403),
        raw_yaml=PIPELINE_WITH_MIXED_INCLUDES,
    )

    sync_gitlab_ci_config(
        neo4j_session,
        TEST_GITLAB_URL,
        "fake-token",
        TEST_UPDATE_TAG,
        _common_job_parameters(),
        projects=[{"id": TEST_PROJECT_ID, "default_branch": "main"}],
        variables_by_project={TEST_PROJECT_ID: project_variables},
    )

    # is_merged should be False (came from raw repository file, not lint).
    configs = check_nodes(
        neo4j_session,
        "GitLabCIConfig",
        ["id", "is_merged"],
    )
    assert configs == {(f"{TEST_PROJECT_ID}:.gitlab-ci.yml", False)}

    # Includes are visible because the raw fixture still has them.
    include_pinning = check_nodes(
        neo4j_session,
        "GitLabCIInclude",
        ["include_type", "is_pinned"],
    )
    assert ("project", True) in include_pinning
    assert ("project", False) in include_pinning

    # USES_INCLUDE edges from config to includes.
    uses_rels = check_rels(
        neo4j_session,
        "GitLabCIConfig",
        "id",
        "GitLabCIInclude",
        "id",
        "USES_INCLUDE",
    )
    assert len(uses_rels) >= 4

    # REFERENCES_VARIABLE — only DATABASE_URL and DEPLOY_TOKEN are in the YAML.
    var_rels = check_rels(
        neo4j_session,
        "GitLabCIConfig",
        "id",
        "GitLabCIVariable",
        "key",
        "REFERENCES_VARIABLE",
    )
    assert {key for _, key in var_rels} == {"DATABASE_URL", "DEPLOY_TOKEN"}

    # The cleanup-scoping RESOURCE edge from project → config still exists.
    # (There is no separate HAS_CI_CONFIG edge — it would duplicate RESOURCE
    # since each project has exactly one CIConfig.)
    config_rels = check_rels(
        neo4j_session,
        "GitLabProject",
        "id",
        "GitLabCIConfig",
        "id",
        "RESOURCE",
    )
    assert config_rels == {(TEST_PROJECT_ID, f"{TEST_PROJECT_ID}:.gitlab-ci.yml")}


def test_sync_ci_config_skips_project_when_no_yaml(neo4j_session, monkeypatch):
    """A project with no readable CI config is skipped without error."""
    _reset_db_and_create_project(neo4j_session)
    # Both /ci/lint and the raw repository file return 404 — the project
    # legitimately has no .gitlab-ci.yml. Mock at the HTTP boundary
    # (`requests.request`) rather than at the internal helper.
    monkeypatch.setattr(
        "cartography.intel.gitlab.util.requests.request",
        lambda method, url, **_: _make_response(404),
    )
    monkeypatch.setattr("cartography.intel.gitlab.util.time.sleep", lambda _: None)

    skipped = sync_gitlab_ci_config(
        neo4j_session,
        TEST_GITLAB_URL,
        "fake-token",
        TEST_UPDATE_TAG,
        _common_job_parameters(),
        projects=[{"id": TEST_PROJECT_ID, "default_branch": "main"}],
        variables_by_project={TEST_PROJECT_ID: []},
    )
    assert check_nodes(neo4j_session, "GitLabCIConfig", ["id"]) == set()
    # 404 is non-denied: cleanup may run on this project.
    assert skipped == set()


def test_sync_ci_config_skips_cleanup_when_lint_and_raw_both_denied(
    neo4j_session, monkeypatch
):
    """A 403 on both endpoints flags the project as denied (skip cleanup)."""
    _reset_db_and_create_project(neo4j_session)
    monkeypatch.setattr(
        "cartography.intel.gitlab.util.requests.request",
        lambda method, url, **_: _make_response(403),
    )
    monkeypatch.setattr("cartography.intel.gitlab.util.time.sleep", lambda _: None)

    skipped = sync_gitlab_ci_config(
        neo4j_session,
        TEST_GITLAB_URL,
        "fake-token",
        TEST_UPDATE_TAG,
        _common_job_parameters(),
        projects=[{"id": TEST_PROJECT_ID, "default_branch": "main"}],
        variables_by_project={TEST_PROJECT_ID: []},
    )
    assert TEST_PROJECT_ID in skipped
