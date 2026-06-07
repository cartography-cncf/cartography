"""Integration tests for GitLab environments module."""

from unittest.mock import patch

from cartography.intel.gitlab.ci_variables import load_project_variables
from cartography.intel.gitlab.ci_variables import transform_variables
from cartography.intel.gitlab.environments import sync_gitlab_environments
from tests.data.gitlab.ci_variables import GET_PROJECT_VARIABLES_RESPONSE
from tests.data.gitlab.environments import GET_ENVIRONMENTS_RESPONSE
from tests.data.gitlab.environments import TEST_GITLAB_URL
from tests.data.gitlab.environments import TEST_PROJECT_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = 10


def _create_project(neo4j_session):
    neo4j_session.run(
        """
        MERGE (p:GitLabProject{id: $project_id, gitlab_url: $gitlab_url})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $update_tag
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


@patch("cartography.intel.gitlab.environments.get_paginated")
def test_sync_environments_creates_env_to_variable_links(
    mock_get_paginated, neo4j_session
):
    """End-to-end: load variables, sync environments, verify exact + wildcard matches."""
    _create_project(neo4j_session)

    # Pre-load project variables (would normally come from the ci_variables sync).
    project_variables = transform_variables(
        GET_PROJECT_VARIABLES_RESPONSE,
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

    mock_get_paginated.return_value = list(GET_ENVIRONMENTS_RESPONSE)

    sync_gitlab_environments(
        neo4j_session,
        TEST_GITLAB_URL,
        "fake-token",
        TEST_UPDATE_TAG,
        _common_job_parameters(),
        projects=[{"id": TEST_PROJECT_ID}],
        variables_by_project={TEST_PROJECT_ID: project_variables},
    )

    expected_envs = {
        (f"{TEST_PROJECT_ID}:1", "production"),
        (f"{TEST_PROJECT_ID}:2", "staging"),
        (f"{TEST_PROJECT_ID}:3", "review/feature-x"),
    }
    assert (
        check_nodes(neo4j_session, "GitLabEnvironment", ["id", "name"]) == expected_envs
    )

    # production env -> DATABASE_URL[production], FEATURE_FLAG[*], CONFIG_FILE[*]
    # staging env    -> DATABASE_URL[staging],   FEATURE_FLAG[*], CONFIG_FILE[*]
    # review/feature-x env -> FEATURE_FLAG[*], CONFIG_FILE[*] (no exact match)
    env_var_rels = check_rels(
        neo4j_session,
        "GitLabEnvironment",
        "name",
        "GitLabCIVariable",
        "id",
        "HAS_CI_VARIABLE",
    )

    var_ids = {v["key"]: v["id"] for v in project_variables}
    db_prod_id = next(
        v["id"]
        for v in project_variables
        if v["key"] == "DATABASE_URL" and v["environment_scope"] == "production"
    )
    db_staging_id = next(
        v["id"]
        for v in project_variables
        if v["key"] == "DATABASE_URL" and v["environment_scope"] == "staging"
    )
    flag_id = var_ids["FEATURE_FLAG"]
    config_id = var_ids["CONFIG_FILE"]

    expected_pairs = {
        ("production", db_prod_id),
        ("production", flag_id),
        ("production", config_id),
        ("staging", db_staging_id),
        ("staging", flag_id),
        ("staging", config_id),
        ("review/feature-x", flag_id),
        ("review/feature-x", config_id),
    }
    assert env_var_rels == expected_pairs

    # Project HAS_ENVIRONMENT -> 3 envs
    project_env_rels = check_rels(
        neo4j_session,
        "GitLabProject",
        "id",
        "GitLabEnvironment",
        "id",
        "HAS_ENVIRONMENT",
    )
    assert {env_id for _, env_id in project_env_rels} == {
        f"{TEST_PROJECT_ID}:1",
        f"{TEST_PROJECT_ID}:2",
        f"{TEST_PROJECT_ID}:3",
    }
