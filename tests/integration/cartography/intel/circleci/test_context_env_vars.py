from unittest.mock import patch

import requests

import cartography.intel.circleci.context_env_vars
import tests.data.circleci.context_env_vars
import tests.data.circleci.contexts
from tests.integration.cartography.intel.circleci.test_contexts import (
    _ensure_local_neo4j_has_test_contexts,
)
from tests.integration.cartography.intel.circleci.test_organizations import (
    _ensure_local_neo4j_has_test_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://circleci.fake/api/v2"
TEST_ORG_ID = "org-1111-aaaa"


def _fake_get(api_session, base_url, context_id):
    return tests.data.circleci.context_env_vars.CIRCLECI_CONTEXT_ENV_VARS[context_id]


@patch.object(
    cartography.intel.circleci.context_env_vars,
    "get",
    side_effect=_fake_get,
)
def test_load_circleci_context_env_vars(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_orgs(neo4j_session)
    _ensure_local_neo4j_has_test_contexts(neo4j_session)

    # Act
    cartography.intel.circleci.context_env_vars.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG_ID,
        tests.data.circleci.contexts.CIRCLECI_CONTEXTS,
    )

    # Assert env vars exist (names only, no values)
    assert check_nodes(neo4j_session, "CircleCIContextEnvVar", ["id", "variable"]) == {
        ("ctx-1:AWS_ACCESS_KEY_ID", "AWS_ACCESS_KEY_ID"),
        ("ctx-1:AWS_SECRET_ACCESS_KEY", "AWS_SECRET_ACCESS_KEY"),
        ("ctx-2:DEPLOY_TOKEN", "DEPLOY_TOKEN"),
    }

    # Assert (Context)-[:HAS_ENV_VAR]->(EnvVar)
    assert check_rels(
        neo4j_session,
        "CircleCIContextEnvVar",
        "id",
        "CircleCIContext",
        "id",
        "HAS_ENV_VAR",
        rel_direction_right=False,
    ) == {
        ("ctx-1:AWS_ACCESS_KEY_ID", "ctx-1"),
        ("ctx-1:AWS_SECRET_ACCESS_KEY", "ctx-1"),
        ("ctx-2:DEPLOY_TOKEN", "ctx-2"),
    }

    # Assert (Org)-[:RESOURCE]->(EnvVar)
    assert check_rels(
        neo4j_session,
        "CircleCIContextEnvVar",
        "id",
        "CircleCIOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("ctx-1:AWS_ACCESS_KEY_ID", TEST_ORG_ID),
        ("ctx-1:AWS_SECRET_ACCESS_KEY", TEST_ORG_ID),
        ("ctx-2:DEPLOY_TOKEN", TEST_ORG_ID),
    }
