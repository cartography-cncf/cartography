"""Integration tests for GitLab CI/CD variables module."""

from unittest.mock import patch

import requests

from cartography.intel.gitlab.ci_variables import sync_gitlab_ci_variables
from tests.data.gitlab.ci_variables import GET_GROUP_VARIABLES_RESPONSE
from tests.data.gitlab.ci_variables import GET_PROJECT_VARIABLES_RESPONSE
from tests.data.gitlab.ci_variables import TEST_GITLAB_URL
from tests.data.gitlab.ci_variables import TEST_GROUP_ID
from tests.data.gitlab.ci_variables import TEST_PROJECT_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = 10


def _reset_db_and_create_group_and_project(neo4j_session):
    """Wipe the shared session DB then create a fresh group + project.

    The neo4j_session fixture is module-scoped, so without a wipe each test
    inherits state from the previous one — the 403-tolerance test would
    otherwise see variables loaded by an earlier test.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n;")
    neo4j_session.run(
        """
        MERGE (g:GitLabGroup{id: $group_id, gitlab_url: $gitlab_url})
        ON CREATE SET g.firstseen = timestamp()
        SET g.lastupdated = $update_tag
        MERGE (p:GitLabProject{id: $project_id, gitlab_url: $gitlab_url})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $update_tag
        """,
        group_id=TEST_GROUP_ID,
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


def _patched_paginated(endpoint, **_kwargs):
    if endpoint == f"/api/v4/groups/{TEST_GROUP_ID}/variables":
        return list(GET_GROUP_VARIABLES_RESPONSE)
    if endpoint == f"/api/v4/projects/{TEST_PROJECT_ID}/variables":
        return list(GET_PROJECT_VARIABLES_RESPONSE)
    return []


@patch("cartography.intel.gitlab.ci_variables.get_paginated")
def test_sync_ci_variables_loads_at_both_scopes(mock_get_paginated, neo4j_session):
    _reset_db_and_create_group_and_project(neo4j_session)
    mock_get_paginated.side_effect = (
        lambda _url, _tok, endpoint, **kw: _patched_paginated(endpoint, **kw)
    )

    project_vars, skipped = sync_gitlab_ci_variables(
        neo4j_session,
        TEST_GITLAB_URL,
        "fake-token",
        TEST_UPDATE_TAG,
        _common_job_parameters(),
        groups=[{"id": TEST_GROUP_ID}],
        projects=[{"id": TEST_PROJECT_ID}],
    )
    assert skipped == {"groups": set(), "projects": set()}

    # All variables loaded — keyed by composite ID, so two DATABASE_URL rows survive.
    expected_keys = {
        ("DEPLOY_TOKEN", True, "*"),
        ("GROUP_OPEN_VAR", False, "*"),
        ("DATABASE_URL", True, "production"),
        ("DATABASE_URL", False, "staging"),
        ("FEATURE_FLAG", False, "*"),
        ("CONFIG_FILE", False, "*"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "GitLabCIVariable",
            ["key", "protected", "environment_scope"],
        )
        == expected_keys
    )

    # Group HAS_CI_VARIABLE relationships (2)
    group_rels = check_rels(
        neo4j_session,
        "GitLabGroup",
        "id",
        "GitLabCIVariable",
        "key",
        "HAS_CI_VARIABLE",
    )
    assert {key for _, key in group_rels} == {"DEPLOY_TOKEN", "GROUP_OPEN_VAR"}

    # Project HAS_CI_VARIABLE — match by composite id so the two DATABASE_URL
    # variants (production / staging) don't collapse in the result set.
    project_rels = check_rels(
        neo4j_session,
        "GitLabProject",
        "id",
        "GitLabCIVariable",
        "id",
        "HAS_CI_VARIABLE",
    )
    assert len(project_rels) == 4

    # Returned map should expose project variables for downstream modules.
    assert TEST_PROJECT_ID in project_vars
    assert len(project_vars[TEST_PROJECT_ID]) == 4


@patch("cartography.intel.gitlab.ci_variables.get_paginated")
def test_sync_ci_variables_does_not_store_value(mock_get_paginated, neo4j_session):
    """A direct Cypher check confirming that no value column was persisted."""
    _reset_db_and_create_group_and_project(neo4j_session)
    mock_get_paginated.side_effect = (
        lambda _url, _tok, endpoint, **kw: _patched_paginated(endpoint, **kw)
    )

    sync_gitlab_ci_variables(
        neo4j_session,
        TEST_GITLAB_URL,
        "fake-token",
        TEST_UPDATE_TAG,
        _common_job_parameters(),
        groups=[{"id": TEST_GROUP_ID}],
        projects=[{"id": TEST_PROJECT_ID}],
    )

    result = neo4j_session.run(
        "MATCH (v:GitLabCIVariable) WHERE v.value IS NOT NULL RETURN count(v) AS c"
    )
    assert result.single()["c"] == 0


@patch("cartography.intel.gitlab.ci_variables.get_paginated")
def test_sync_ci_variables_tolerates_403_per_scope(mock_get_paginated, neo4j_session):
    """A 403 on the group scope should not break the project sync."""
    _reset_db_and_create_group_and_project(neo4j_session)

    def side_effect(_url, _tok, endpoint, **_kw):
        if endpoint == f"/api/v4/groups/{TEST_GROUP_ID}/variables":
            response = requests.Response()
            response.status_code = 403
            raise requests.exceptions.HTTPError(response=response)
        return _patched_paginated(endpoint)

    mock_get_paginated.side_effect = side_effect

    sync_gitlab_ci_variables(
        neo4j_session,
        TEST_GITLAB_URL,
        "fake-token",
        TEST_UPDATE_TAG,
        _common_job_parameters(),
        groups=[{"id": TEST_GROUP_ID}],
        projects=[{"id": TEST_PROJECT_ID}],
    )

    # Group variables skipped, project variables still loaded.
    group_rels = check_rels(
        neo4j_session,
        "GitLabGroup",
        "id",
        "GitLabCIVariable",
        "key",
        "HAS_CI_VARIABLE",
    )
    assert group_rels == set()

    project_rels = check_rels(
        neo4j_session,
        "GitLabProject",
        "id",
        "GitLabCIVariable",
        "id",
        "HAS_CI_VARIABLE",
    )
    assert len(project_rels) == 4
