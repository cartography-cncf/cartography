from unittest.mock import patch

import requests

import cartography.intel.circleci.components
import cartography.intel.circleci.environments
import tests.data.circleci.environments
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


@patch.object(
    cartography.intel.circleci.environments,
    "get",
    return_value=tests.data.circleci.environments.CIRCLECI_ENVIRONMENTS,
)
def test_load_circleci_environments(mock_api, neo4j_session):
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_orgs(neo4j_session)

    cartography.intel.circleci.environments.sync(
        neo4j_session, api_session, common_job_parameters, TEST_ORG_ID
    )

    assert check_nodes(neo4j_session, "CircleCIEnvironment", ["id", "name"]) == {
        ("env-1", "production"),
    }
    # labels are flattened from [{key,value}] objects to "key=value" strings
    labels = neo4j_session.run(
        "MATCH (e:CircleCIEnvironment {id: 'env-1'}) RETURN e.labels AS labels"
    ).single()["labels"]
    assert labels == ["env=prod"]
    assert check_rels(
        neo4j_session,
        "CircleCIEnvironment",
        "id",
        "CircleCIOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("env-1", TEST_ORG_ID),
    }


@patch.object(
    cartography.intel.circleci.components,
    "get",
    return_value=tests.data.circleci.environments.CIRCLECI_COMPONENTS,
)
def test_load_circleci_components(mock_api, neo4j_session):
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_orgs(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    cartography.intel.circleci.components.sync(
        neo4j_session, api_session, common_job_parameters, TEST_ORG_ID
    )

    assert check_nodes(neo4j_session, "CircleCIComponent", ["id", "name"]) == {
        ("comp-1", "web-service"),
    }
    # (Org)-[:RESOURCE]->(Component)
    assert check_rels(
        neo4j_session,
        "CircleCIComponent",
        "id",
        "CircleCIOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("comp-1", TEST_ORG_ID),
    }
    # (Project)-[:HAS_COMPONENT]->(Component)
    assert check_rels(
        neo4j_session,
        "CircleCIComponent",
        "id",
        "CircleCIProject",
        "id",
        "HAS_COMPONENT",
        rel_direction_right=False,
    ) == {
        ("comp-1", "proj-1"),
    }
