from unittest.mock import patch

import requests

import cartography.intel.circleci.contexts
import tests.data.circleci.contexts
from tests.integration.cartography.intel.circleci.test_organizations import (
    _ensure_local_neo4j_has_test_orgs,
)
from tests.integration.cartography.intel.circleci.test_projects import (
    _ensure_local_neo4j_has_test_projects,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://circleci.fake/api/v2"
TEST_ORG_ID = "org-1111-aaaa"


def _ensure_local_neo4j_has_test_contexts(neo4j_session):
    contexts = cartography.intel.circleci.contexts.transform(
        tests.data.circleci.contexts.CIRCLECI_CONTEXTS,
    )
    cartography.intel.circleci.contexts.load_contexts(
        neo4j_session,
        contexts,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.circleci.contexts,
    "get_restricted_project_ids",
    return_value=[],
)
@patch.object(
    cartography.intel.circleci.contexts,
    "get",
    return_value=tests.data.circleci.contexts.CIRCLECI_CONTEXTS,
)
def test_load_circleci_contexts(mock_api, mock_restrictions, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_orgs(neo4j_session)

    # Act
    cartography.intel.circleci.contexts.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG_ID,
    )

    # Assert contexts exist
    assert check_nodes(neo4j_session, "CircleCIContext", ["id", "name"]) == {
        ("ctx-1", "build-secrets"),
        ("ctx-2", "deploy-secrets"),
    }

    # Assert (Org)-[:RESOURCE]->(Context)
    assert check_rels(
        neo4j_session,
        "CircleCIContext",
        "id",
        "CircleCIOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("ctx-1", TEST_ORG_ID),
        ("ctx-2", TEST_ORG_ID),
    }


@patch.object(
    cartography.intel.circleci.contexts,
    "get",
    return_value=tests.data.circleci.contexts.CIRCLECI_CONTEXTS,
)
def test_circleci_context_restricted_to_project(mock_api, neo4j_session):
    """A context restricted to a project links via RESTRICTED_TO (one-to-many)."""
    # Arrange: ctx-1 is restricted to proj-1 (which must already exist).
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_orgs(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    restrictions = {"ctx-1": ["proj-1"], "ctx-2": []}
    with patch.object(
        cartography.intel.circleci.contexts,
        "get_restricted_project_ids",
        side_effect=lambda api, base_url, context_id: restrictions[context_id],
    ):
        cartography.intel.circleci.contexts.sync(
            neo4j_session,
            api_session,
            common_job_parameters,
            TEST_ORG_ID,
        )

    # Assert (Context)-[:RESTRICTED_TO]->(Project)
    assert check_rels(
        neo4j_session,
        "CircleCIContext",
        "id",
        "CircleCIProject",
        "id",
        "RESTRICTED_TO",
        rel_direction_right=True,
    ) == {
        ("ctx-1", "proj-1"),
    }
